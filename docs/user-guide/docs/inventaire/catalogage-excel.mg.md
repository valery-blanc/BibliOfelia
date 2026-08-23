# Katalaogy avy amin'ny Excel

Tonga ao amin'ny tetikasa Ofelia ny tranomboky maro miaraka amin'ny fonosam-
boky efa voasoratra ao anaty **rakitra Excel** (kaody anaty, lohateny,
mpanoratra, indraindray ISBN). Manolotra fitaovana efatra hampiasana io rakitra
io ny **katalaogy Excel** :

1. **Hamarina rakitra** — manisy fanamarihana ny rakitra Excel-nao ny
   BibliOfelia amin'izay fantatry ny banky angona an-tserasera momba ny boky
   tsirairay, nefa tsy manova na inona na inona ao amin'ny katalaogy. Tena
   mety **alohan'ny** fifindrana, mba handrefesana ny kalitaon'ny rakitra sy
   hanitsiana azy an-tanana.
2. **Afaro ao amin'ny katalaogy** — ovain'ny BibliOfelia ho notice sy kopia
   ilay lisitra ISBN, indray mandeha.
3. **Havoaka ny katalaogy** — averin'ny BibliOfelia aminao amin'ny rakitra
   Excel ny fonosam-bokinao manontolo, andalana iray isaky ny kopia.
4. **Hanavao kopia** — averinao ilay rakitra voahitsy, dia ampiharin'ny
   BibliOfelia amin'ny boky efa voasoratra ao amin'ny katalaogy ny
   fanitsianao, nefa tsy mamorona boky vaovao mihitsy.

!!! info "Ho an'ny mpitantana tranomboky ihany"
    Ao amin'ny menu **Mandroso** no misy ny katalaogy Excel, azon'ny
    mpitantana tranomboky sy ny mpitantana ampiasaina.

## Hanokatra ny katalaogy Excel

Avy ao amin'ny menu [**Mandroso**](/bibliofelia/mg/advanced/){ target="_blank" },
fizarana **Fanisana**, tsindrio
[**Katalaogy Excel**](/bibliofelia/mg/catalog/excel-catalog/){ target="_blank" }.

Mampiseho boaty efatra ny pejy : **Hamarina rakitra**, **Afaro ao amin'ny
BibliOfelia**, **Havoaka ny katalaogy** ary **Hanavao kopia**.

## Hamarina rakitra

Ampiasao mba **hijery** rakitra Excel nefa tsy mikasika ny katalaogy.

Ny rakitrao dia tsy maintsy **`.xlsx`** ka ny andalana voalohany dia mirakitra
farafahakeliny ireto tsanganana efatra ireto (azo ekena ny renisoratra
sy ny tsindrim-peo) :

| Tsanganana | Votoatiny |
|---|---|
| `ID` | ny kaody anatinao (tehirizina toy izany) |
| `TITLE` | ny lohatenin'ny boky |
| `AUTHOR` | ny mpanoratra |
| `ISBN` | ny ISBN feno (isa 10 na 13) |

!!! warning "ISBN tsy feno na diso"
    Ny fikarohana amin'ny ISBN dia tsy mandray afa-tsy ISBN **mety** (isa 10
    na 13). Ny ISBN tsy feno na diso dia voamariky ny `ISBN_INVALID` ka
    **tsy** ahafahana mahita ny boky amin'ny ISBN — izay indrindra no toe-
    javatra ratsy indrindra. Amin'izay dia ny `TITLE` sy ny `AUTHOR` no
    mamonjy, amin'ny alalan'ny fikarohana amin'ny lohateny + mpanoratra :
    karakarao tsara ireo tsanganana roa ireo.

Ao amin'ny boaty
[**Hamarina rakitra**](/bibliofelia/mg/catalog/excel-catalog/){ target="_blank" },
fidio ny rakitrao dia tsindrio **Atombohy ny fanamarinana**.

Manontany ny **OpenLibrary, Google Books, BNF ary BNE** ny BibliOfelia,
amin'ny ISBN aloha, dia amin'ny lohateny + mpanoratra. Atao ao ambadika ny
fanodinana : manodidina ny **10 minitra isaky ny andalana 300**.

Rehefa vita ny asa, tsindrio **Alaivo ny rakitra misy fanamarihana**.
Azonao indray ny rakitra Excel tany am-boalohany, voamp'efan'ny tsanganana
fanampiny :

- `TITLE_FOUND_BY_ISBN`, `AUTHOR_FOUND_BY_ISBN`, `SOURCE_BY_ISBN` — izay hita
  noho ny ISBN ;
- `ISBN_FOUND_BY_TA`, `TITLE_FOUND_BY_TA`, `AUTHOR_FOUND_BY_TA` — izay hitan'ny
  fikarohana amin'ny lohateny + mpanoratra ;
- `CONFIDENCE` — isa 0 ka hatramin'ny 100 momba ny fahatokisana ny
  fifanarahana.

!!! tip "Vakio ny loko"
    Miseho **volontany** ny sela manana isa fahatokisana ambany : ireo no
    andalana tokony hojerena an-tanana. Ny `ISBN_FOUND_BY_TA` tsy mitovy
    amin'ny ISBN-nao matetika dia manondro **hadisoana** tao amin'ny rakitra
    tany am-boalohany.

Ny fanamarinana dia **tsy manoratra na inona na inona** ao amin'ny katalaogy
: azonao atao imbetsaka araka izay ilainao.

## Afaro ao amin'ny katalaogy

Ampiasao mba **hamorona** marina ny notice sy ny kopia avy amin'ny lisitra
ISBN.

Ny rakitra `.xlsx`-nao dia tsy maintsy misy farafahakeliny tsanganana
**`ISBN`** iray. **Tsy voatery** ny tsanganana hafa rehetra : ampio ihany
izay anananao, na inona na inona filaharana.

| Tsanganana | Votoatiny |
|---|---|
| `ISBN` | **tsy maintsy** |
| `LOCATION` | kaody toerana (raha tsy izany dia noforonina tsy misy toerana ny kopia) |
| `CATEGORY` | anaran'ny sokajy efa misy |
| `TITLE` | lohatenin'ny rakitra |
| `AUTHOR` | mpanoratra, sarahina amin'ny **teboka sy faingo (;)** |
| `TYPE` | karazana boky (Boky, BD / manga, Gazetiboky, Gazety, CD audio, Hafa) |
| `EDITOR` | mpamoaka |
| `YEAR` | taona namoahana |
| `LANGUAGE` | kaody fiteny (fr, en, es…) |
| `TAGS` | teny fanalahidy sarahina amin'ny **faingo** |
| `EXTERNAL_CODE` | ny kaodin'ny tranomboky hafa efa eo amin'ny boky |
| `PROVENANCE` | ny kaody na ny anaran'ny fiaviana efa misy |
| `CATEGORY_ABBR` | ny fanafohezan'ny sokajy (kaody talantalana) |
| `CONDITION` | toetran'ny kopia (Vaovao, Tsara, Simba kely, Simba) |

Ao amin'ny boaty
[**Afaro ao amin'ny BibliOfelia**](/bibliofelia/mg/catalog/excel-catalog/){ target="_blank" },
fidio ny rakitrao dia tsindrio **Afaro ao amin'ny katalaogy**.

Lasa notice sy kopia ny ISBN tsirairay. Raha **efa misy** ao amin'ny
katalaogy ny ISBN iray, dia tsy averin'ny BibliOfelia foronina ny notice :
manampy kopia fotsiny amin'ny notice efa misy izy.

!!! info "Ny tsanganana feno dia manolo ny mombamomba ao amin'ny rakitra"
    Raha manampy iray amin'ireo tsanganana etsy ambony ianao (lohateny,
    mpanoratra, mpamoaka…) ka **feno ny sela**, dia **manolo** ny saha
    mifanaraka ao amin'ny rakitra ny sandany — **na dia efa misy aza ny
    notice**. Ny **sela banga dia tsy manova na inona na inona** : voatahiry
    ny mombamomba efa misy. Ho an'ny mpanoratra sy ny tags, dia **manolo** ny
    lisitra efa misy ny an'ny rakitra (fa tsy manampy aminy). Ny sanda tsy
    fantatra ho an'ny `TYPE` na `CONDITION`, na taona tsy isa, dia
    **tsy raharahaina** ka voamarika ao amin'ny fampilazana momba ny andiana.

Ny fanafarana dia mamorona **andian-katalaogy** : rehefa vita ny asa,
tsindrio **Hijery ny andiana nafarana** mba hanokatra azy, na tadiavo ao
amin'ny
[**Katalaogy amin'ny scan**](/bibliofelia/mg/catalog/scan/){ target="_blank" },
toy ny andiana voa-scan tamin'ny caméra.

!!! tip "Hameno izay tsy ampy an-tserasera"
    ISBN ihany no anananao, tsy misy lohateny na mpanoratra? Atombohy avy eo
    ny **fampitomboana** amin'ilay andiana mba haka ny metadata an-tserasera
    (OpenLibrary, Google Books, BnF…). Mitana ny laharam-pahamehana ny
    tsanganan'ny rakitra : ny fampitomboana dia mameno ihany izay mbola banga.

## Havoaka ny katalaogy

Ampiasao mba **hahazoana indray ny fonosam-bokinao manontolo** amin'ny rakitra
Excel : hamakiana azy, hitahirizana kopia tsy mila aterineto, na
hanomanana fanitsiana be dia be.

Ao amin'ny boaty **Havoaka ny katalaogy**, tsindrio ny **Havoaka ny
katalaogy**. Midina avy hatrany ny rakitra `catalogue-AAAA-MM-JJ.xlsx` : tsy
misy andrasana.

Misy **andalana iray isaky ny kopia** ilay rakitra, fa tsy isaky ny
lohateny. Ny boky iray anananao kopia telo dia mandray andalana telo :
ara-dalàna izany, satria ny toerana, ny toe-javatra, ny fiaviana ary ny kaody
ivelany dia an'ny **kopia**, fa tsy an'ny raki-tsoratra.

| Fariana | Votoatiny |
|---|---|
| `OFELIA_CODE` | ny kaody Ofelia an'ny kopia (ny kaody tsora-tsoratra eo amin'ny marika) |
| `INTERNAL_ID` | ny kaody vakina voasoratra eo akaikin'ny kaody tsora-tsoratra (`OFL-…`) |
| `EXTERNAL_CODE` | ny kaody avy amin'ny tranomboky hafa efa eo amin'ny boky |
| `ISBN`, `TITLE`, `AUTHOR`, `EDITOR`, `YEAR`, `LANGUAGE` | ny mombamomba ny raki-tsoratra |
| `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `TAGS` | ny fanasokajiana |
| `CONDITION`, `PROVENANCE`, `LOCATION` | ny mombamomba ny kopia |

!!! tip "Izy no rakitra ampiasaina amin'ny fanavaozana"
    Ireo fariana avoaka dia **mitovy tanteraka** amin'izay hain'ny BibliOfelia
    vakina indray. Ahitsio ao amin'ny Excel izay tianao, dia averino amin'ny
    **Hanavao kopia** ilay rakitra : tsy misy hafa homanina.

## Hanavao kopia

Ampiasao mba **hanitsiana betsaka** ny boky **efa** ao amin'ny katalaogy :
hanova toerana rehefa nafindra ny talantalana, hanova andiany ho
« Simba kely », hanome kaody ivelany, hanitsy lohateny voasoratra ratsy.

!!! success "Tsy misy boky foronina"
    Tsy mamorona raki-tsoratra na kopia **mihitsy** ity fitaovana ity. Raha
    manondro kopia tsy misy ny andalana iray, dia **tsindriana** izy ka
    avela : tsy atao boky vaovao velively. Azonao averina àry ny rakitra
    navoaka, tsy misy loza hampitovy roa ny tranombokinao.

Tsy maintsy milaza **kopia inona no resahiny** ny andalana tsirairay. Tsy
maintsy misy farafahakeliny iray amin'ireto fariana roa ireto àry ny rakitra :

| Fariana | Votoatiny |
|---|---|
| `OFELIA_CODE` | ny kaody Ofelia an'ny kopia : ny kaody tsora-tsoratra `290…` **na** ny kaody vakina `OFL-…` |
| `EXTERNAL_CODE` | ny kaody avy amin'ny tranomboky hafa eo amin'ny boky |

!!! info "Raha feno izy roa"
    Ny **kaody Ofelia** no manondro ny kopia, ary **ampiharina aminy** ny
    kaody ivelany eo amin'ilay andalana. Izany no fomba anomezana kaody
    ivelany boky maro miaraka : fariana `OFELIA_CODE` hilazana hoe boky
    inona, fariana `EXTERNAL_CODE` misy ny kaody hapetraka.

Ekena ary **tsy voatery** ireo fariana hafa rehetra amin'ny fampidirana :
`TITLE`, `AUTHOR`, `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `EDITOR`, `YEAR`,
`LANGUAGE`, `TAGS`, `CONDITION`, `PROVENANCE`, `LOCATION` ary `ISBN`.

!!! warning "Tsy mamafa na inona na inona ny efitra foana"
    Ny efitra **feno** dia manolo ny sanda misy ; ny efitra **foana** kosa
    mamela ny sanda eo. **Tsy** azo ampiasaina hamafana fariana àry ity
    fitaovana ity : sokafy ny pejin'ny boky raha izany. Izany no ahafahanao
    mamerina rakitra navoaka manontolo na dia fariana roa ihany aza no
    nahitsinao.

Fidio ny rakitrao, tsindrio ny **Hanavao ireo kopia**, dia araho toy ny
fampidirana ilay asa. Mampiseho ireto ny pejy antsipiriany :

- **Kopia novaina** — ny andalana tena nanova zavatra ;
- **Andalana tsy niova** — hita ny kopia, saingy efa nilaza toy ny katalaogy
  ihany ny rakitra ;
- **Hadisoana** — ny andalana tsy nampiharina, misy sora-baventy mena sy ny
  antsipiriany ao ambany.

| Fampitandremana | Dikany |
|---|---|
| `OFELIA_CODE_UNKNOWN` | tsy misy kopia mitondra io kaody Ofelia io — nalaina an-tsirambina ny andalana |
| `EXTERNAL_CODE_UNKNOWN` | tsy misy kopia mitondra io kaody ivelany io — nalaina an-tsirambina ny andalana |
| `NO_KEY` | tsy milaza izay kopia resahiny ny andalana |
| `EXTERNAL_CODE_DUPLICATE` | efa eo amin'ny boky hafa io kaody ivelany io — tsy nampiharina izy, fa nampiharina ny ambin'ny andalana |
| `ISBN_CONFLICT` | efa an'ny raki-tsoratra hafa io ISBN io — tsy nampiharina, fa nampiharina ny ambiny |
| `LOCATION_UNKNOWN`, `CATEGORY_UNKNOWN`, `PROVENANCE_UNKNOWN` | tsy misy ao amin'ny lisitrao ny sanda — nalaina an-tsirambina, nampiharina ny ambiny |

!!! tip "Raki-tsoratra iray, kopia maromaro"
    Ny lohateny, ny mpanoratra na ny mpanonta dia an'ny **raki-tsoratra** :
    ny fanitsiana azy eo amin'ny andalan'ny kopia iray dia manitsy azy ho
    an'ny kopia **rehetra** amin'io boky io. Ny toerana, ny toe-javatra, ny
    fiaviana ary ny kaody ivelany kosa dia tsy mikasika afa-tsy ny kopia eo
    amin'io andalana io.

## Araho ny asanao

Eo ambanin'ny pejy
[**Katalaogy Excel**](/bibliofelia/mg/catalog/excel-catalog/){ target="_blank" },
ny fizarana **Asa vao haingana** dia mitanisa ny fanamarinana sy fanafarana
farany nataonao. Tsindrio **Antsipiriany** mba hanaraha ny fandrosoana,
haka rakitra misy fanamarihana na hijery ny fampitandremana isaky ny
andalana.

## Tsara ho fantatra

!!! warning "Endrika sy fetra"
    - Ny rakitra **`.xlsx`** ihany no ekena (tsy misy `.xls`, `.csv` na
      `.ods`).
    - Habe ambony indrindra : **5 Mo**, **andalana 10 000**.
    - Mba hahatsara ny fandrakofana ny ISBN, azon'ny mpitantana
      apetraka ny **lakilen'ny Google Books** ; raha tsy misy izany, dia
      mety hisy andalana vitsivitsy tsy feno noho ny fetra (tsanganana
      `SOURCE_BY_ISBN` = `RATE_LIMITED`). Avereno atao ny ampitso : miverina
      isan'andro ny fetra.

## Jereo koa

- [Catalogue amin'ny scan](catalogage-scan.md) — ny fanafarana mitovy, fa
  amin'ny caméra isaky ny boky
- [Manampy boky](../catalogue/ajouter-livre.md) — mamorona notice tokana
  an-tanana
