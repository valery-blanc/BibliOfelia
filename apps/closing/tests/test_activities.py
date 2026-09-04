"""Activités, animations, présences et statistiques. FEAT-085."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.accounts.models import Role
from apps.closing import services
from apps.closing.models import (
    ActivityEntry,
    ActivityType,
    AnimationAttendance,
    AnimationSession,
    AnimationType,
)
from apps.members.lookup import find_members_by_code
from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def superadmin(django_user_model):
    return django_user_model.objects.create_user(
        username="chef", password="motdepasse123", role=Role.SUPERADMIN
    )


@pytest.fixture
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Marie", last_name="Curie", category=category
    )


@pytest.fixture
def activity_type():
    return ActivityType.objects.create(label="Rangement")


@pytest.fixture
def animation_type():
    return AnimationType.objects.create(label="Heure du conte")


# ----------------------------------------------------------------------
# Saisie des activités
# ----------------------------------------------------------------------
def test_activity_is_stored_in_minutes(client, librarian, activity_type):
    client.force_login(librarian)
    resp = client.post("/fr/closing/activities/", {
        "activity_type": activity_type.pk, "hours": "1", "minutes_part": "30",
        "occurred_on": date.today().isoformat(), "note": "",
    })
    assert resp.status_code == 302
    assert ActivityEntry.objects.get().minutes == 90


def test_activity_requires_a_duration(client, librarian, activity_type):
    client.force_login(librarian)
    resp = client.post("/fr/closing/activities/", {
        "activity_type": activity_type.pk, "hours": "0", "minutes_part": "0",
        "occurred_on": date.today().isoformat(), "note": "",
    })
    assert resp.status_code == 200
    assert ActivityEntry.objects.count() == 0


def test_retroactive_entry_is_allowed(client, librarian, activity_type):
    """Un employé qui a oublié sa journée doit pouvoir la rattraper."""
    yesterday = date.today() - timedelta(days=3)
    client.force_login(librarian)
    client.post("/fr/closing/activities/", {
        "activity_type": activity_type.pk, "hours": "2", "minutes_part": "0",
        "occurred_on": yesterday.isoformat(), "note": "",
    })
    assert ActivityEntry.objects.get().occurred_on == yesterday


def test_future_entry_is_refused(client, librarian, activity_type):
    tomorrow = date.today() + timedelta(days=1)
    client.force_login(librarian)
    resp = client.post("/fr/closing/activities/", {
        "activity_type": activity_type.pk, "hours": "2", "minutes_part": "0",
        "occurred_on": tomorrow.isoformat(), "note": "",
    })
    assert resp.status_code == 200
    assert ActivityEntry.objects.count() == 0


def test_deactivated_type_keeps_past_entries(librarian, activity_type):
    ActivityEntry.objects.create(
        user=librarian, activity_type=activity_type, minutes=60
    )
    activity_type.is_active = False
    activity_type.save(update_fields=["is_active"])
    # Désactiver une nature ne doit pas réécrire l'histoire.
    stats = services.activity_stats(date.today(), date.today())
    assert stats[0]["label"] == "Rangement"
    assert stats[0]["minutes"] == 60


# ----------------------------------------------------------------------
# Animations
# ----------------------------------------------------------------------
def test_presenter_can_create_a_new_animation_label(client, librarian):
    client.force_login(librarian)
    resp = client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "Atelier dessin",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
    })
    assert resp.status_code == 302
    assert AnimationType.objects.get().label == "Atelier dessin"


def test_new_label_matching_is_case_insensitive(librarian, animation_type):
    """Sinon « Heure du conte » et « heure du conte » compteraient à part."""
    again = AnimationType.get_or_create_by_label("heure du conte", user=librarian)
    assert again.pk == animation_type.pk
    assert AnimationType.objects.count() == 1


def test_animation_requires_a_label(client, librarian):
    client.force_login(librarian)
    resp = client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
    })
    assert resp.status_code == 200
    assert AnimationSession.objects.count() == 0


# ----------------------------------------------------------------------
# Présences
# ----------------------------------------------------------------------
def test_last_four_digits_find_the_member(member):
    suffix = member.card_number[-4:]
    assert find_members_by_code(suffix) == [member]


def test_full_card_number_finds_the_member(member):
    assert find_members_by_code(member.card_number) == [member]


def test_ambiguous_suffix_returns_every_candidate(category):
    """Deviner ferait compter la mauvaise personne dans les statistiques."""
    a = Member.objects.create(first_name="Marie", last_name="Curie", category=category)
    b = Member.objects.create(first_name="Pierre", last_name="Curie", category=category)
    Member.objects.filter(pk=a.pk).update(card_number="2910000001234")
    Member.objects.filter(pk=b.pk).update(card_number="2915000001234")
    assert len(find_members_by_code("1234")) == 2


def test_attendance_is_added_by_suffix(client, librarian, animation_type, member):
    session = AnimationSession.objects.create(
        animation_type=animation_type, presenter=librarian, minutes=60
    )
    client.force_login(librarian)
    resp = client.post(f"/fr/closing/animations/{session.pk}/attendee/", {
        "code": member.card_number[-4:],
    })
    assert resp.status_code == 302
    assert AnimationAttendance.objects.filter(
        session=session, member=member
    ).exists()


def test_the_same_member_is_not_counted_twice(client, librarian, animation_type, member):
    session = AnimationSession.objects.create(
        animation_type=animation_type, presenter=librarian, minutes=60
    )
    client.force_login(librarian)
    for _ in range(3):
        client.post(f"/fr/closing/animations/{session.pk}/attendee/", {
            "code": member.card_number,
        })
    assert AnimationAttendance.objects.count() == 1


def test_unknown_code_adds_nobody(client, librarian, animation_type):
    session = AnimationSession.objects.create(
        animation_type=animation_type, presenter=librarian, minutes=60
    )
    client.force_login(librarian)
    client.post(f"/fr/closing/animations/{session.pk}/attendee/", {"code": "0000000"})
    assert AnimationAttendance.objects.count() == 0


# ----------------------------------------------------------------------
# Statistiques
# ----------------------------------------------------------------------
def test_stats_do_not_multiply_non_members_by_attendance(
    librarian, animation_type, category
):
    """Garde-fou contre la jointure : agréger présences et non-membres dans le
    même `aggregate` multiplierait `non_member_adults` par le nombre de
    présents."""
    session = AnimationSession.objects.create(
        animation_type=animation_type, presenter=librarian, minutes=60,
        non_member_adults=4, non_member_children=6,
    )
    for i in range(3):
        member = Member.objects.create(
            first_name=f"P{i}", last_name="Test", category=category
        )
        AnimationAttendance.objects.create(session=session, member=member)
    stats = services.animation_stats(date.today(), date.today())
    assert stats.sessions == 1
    assert stats.member_attendance == 3
    assert stats.non_member_adults == 4
    assert stats.non_member_children == 6
    assert stats.total_attendance == 13


def test_monthly_rows_cover_twelve_months(librarian, animation_type):
    AnimationSession.objects.create(
        animation_type=animation_type, presenter=librarian, minutes=60,
        occurred_on=date(date.today().year, 3, 15), non_member_adults=2,
    )
    rows = services.monthly_rows(date.today().year)
    assert len(rows) == 12
    assert rows[2].sessions == 1
    assert rows[2].non_members == 2


def test_stats_page_renders(client, librarian):
    client.force_login(librarian)
    assert client.get("/fr/closing/stats/").status_code == 200


def test_stats_csv_downloads(client, librarian):
    client.force_login(librarian)
    resp = client.get("/fr/closing/stats/csv/")
    assert resp.status_code == 200
    assert "text/csv" in resp["Content-Type"]


def test_type_referential_is_superadmin_only(client, librarian, superadmin):
    client.force_login(librarian)
    assert client.get("/fr/closing/types/").status_code == 403
    client.force_login(superadmin)
    assert client.get("/fr/closing/types/").status_code == 200

# ----------------------------------------------------------------------
# Présences saisies dès la création (complément 2026-09-01)
# ----------------------------------------------------------------------
def test_attendees_can_be_entered_on_the_creation_form(client, librarian, member):
    """Demande Val : un champ de saisie (+ scan) sur le formulaire, sans
    attendre l'écran de détail."""
    client.force_login(librarian)
    resp = client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "Atelier peinture",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
        "attendee_codes": member.card_number,
    })
    assert resp.status_code == 302
    session = AnimationSession.objects.get()
    assert list(session.attendances.values_list("member_id", flat=True)) == [member.pk]


def test_several_codes_separated_by_spaces_or_commas(client, librarian, category):
    a = Member.objects.create(first_name="A", last_name="Un", category=category)
    b = Member.objects.create(first_name="B", last_name="Deux", category=category)
    client.force_login(librarian)
    client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "Atelier collage",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
        "attendee_codes": f"{a.card_number}, {b.card_number}",
    })
    assert AnimationSession.objects.get().attendances.count() == 2


def test_the_same_code_twice_counts_once(client, librarian, member):
    client.force_login(librarian)
    client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "Atelier double",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
        "attendee_codes": f"{member.card_number} {member.card_number}",
    })
    assert AnimationSession.objects.get().attendances.count() == 1


def test_an_unknown_code_is_reported_and_the_session_is_kept(
    client, librarian, member
):
    """Un code raté ne doit ni faire échouer l'enregistrement, ni disparaître
    en silence."""
    client.force_login(librarian)
    resp = client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "Atelier signale",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
        "attendee_codes": f"{member.card_number} 999999",
    }, follow=True)
    session = AnimationSession.objects.get()
    assert session.attendances.count() == 1
    texts = [m.message for m in resp.context["messages"]]
    assert any("999999" in t for t in texts)


def test_an_ambiguous_code_is_not_guessed(client, librarian, category):
    """Une présence mal attribuée fausserait les statistiques sans que
    personne ne s'en aperçoive."""
    a = Member.objects.create(first_name="A", last_name="Un", category=category)
    b = Member.objects.create(first_name="B", last_name="Deux", category=category)
    Member.objects.filter(pk=a.pk).update(card_number="2910000005678")
    Member.objects.filter(pk=b.pk).update(card_number="2915000005678")
    client.force_login(librarian)
    resp = client.post("/fr/closing/animations/", {
        "animation_type": "", "new_animation": "Atelier ambigu",
        "hours": "1", "minutes_part": "0",
        "occurred_on": date.today().isoformat(),
        "non_member_adults": "0", "non_member_children": "0", "note": "",
        "attendee_codes": "5678",
    }, follow=True)
    assert AnimationSession.objects.get().attendances.count() == 0
    texts = [m.message for m in resp.context["messages"]]
    assert any("5678" in t for t in texts)


def test_the_creation_form_carries_the_field_and_the_scan_button(client, librarian):
    client.force_login(librarian)
    html = client.get("/fr/closing/animations/").content.decode("utf-8")
    assert 'name="attendee_codes"' in html
    assert "js-scan-handoff" in html
    assert 'data-scan-append="true"' in html
