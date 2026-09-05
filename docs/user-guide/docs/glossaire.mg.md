# Voambolana

Voambolana kely an'ireo teny ampiasaina ao amin'ny BibliOfelia.

## Ireo code samihafa: ho an'ny inona?

Ny BibliOfelia dia mampiasa code karazany maro mba hahafantarana
ny boky sy ny mpianatra. Tena ilaina ny mampifandanja azy ireo
satria tsy mitovy ny tanjony.

### Code Ofelia (eo amin'ny etikety sy karatra)

Io no **code-barre** jerena amin'ny scanner na OfeliaScan.
Manomboka amin'ny **290** ho an'ny boky, na **291** ho an'ny karatra
mpianatra. Misy isa 13 ny totaliny.

Ohatra:

- `2900000000017` → etikety boky
- `2910000000444` → karatry ny mpianatra

Io no code aforonin'ny BibliOfelia automatika rehefa mamorona kopia
vaovao na mpianatra vaovao ianao. Io no soratana amin'ny etikety
sy ny karatra ara-batana. Io no jerena ho an'ny fampindramana,
famerenana, récolement.

Rehefa voatonta, tsy miova mihitsy ity code ity. Raha very ny
etikety na ny karatra, **tsy atontaonao ny mitovy**: mamorona vaovao
miaraka amin'ny code hafa (jereo [Boky
very](faq.md#livre-perdu) sy [Karatra
very](faq.md#carte-perdue)).

### Code interne (eo amin'ny takelaky ny boky, fa tsy eo amin'ny etikety)

Eo akaikin'ny code Ofelia, ny boky tsirairay koa dia manana **code
interne** mora vakiana kokoa ho an'ny mpitantana tranomboky.
Manana endrika **OFL-AAAAMMDD-NNNN**:

- `OFL-20260525-0014` → boky faha-14 nampidirina ny 25 may 2026

Ity code ity dia miseho ao amin'ny BibliOfelia amin'ny takelakan'ny
kopia. Ahafahana mahafantatra haingana hoe rahoviana no nampidirina
ny boky. Tsy atontana amin'ny etikety, fa **azonao soratana** ao
amin'ny fikarohana, fampindramana na famerenana — misy na tsy misy
tsipika.

### ISBN-13 (eo amin'ny couverture an'ny boky, voatonta ny editora)

Io no code 13 isa izay atontaona **editora** eo amin'ny ambadiky
ny boky, matetika akaikin'ny code-barre standard. Mahafantatra ny
lohateny manerantany.

Ohatra: `9782070612758` → mahafantatra ny *Le Petit Prince* an'i
Gallimard.

Rehefa mamorona notice vaovao ianao, ny BibliOfelia dia manontany
ny base OpenLibrary avy amin'ny ISBN-13 mba hameno ny lohateny, ny
mpanoratra ary ny editora. Ny ISBN-13 dia ampiasaina indrindra ho
an'ny **catalogage**, fa tsy ho an'ny fampindramana isan'andro.

Ho an'ny fampindramana, ny code Ofelia an'ny boky no jerena, **fa
tsy ny ISBN** (boky iray dia afaka manana kopia 3: mitovy ny ISBN,
fa tsirairay manana ny code Ofeliany).

### ISBN-10 (endrika taloha)

Talohan'ny 2007, ny boky dia nanana code editora 10 isa: io ny
ISBN-10. Mety hahita izany ianao amin'ny boky taloha. Ny BibliOfelia
dia mandray ny roa: raha manoratra ISBN-10 ianao, dia voadika
automatika ho ISBN-13.

### ISSN (gazetiboky sy gazety)

Ny **ISSN** dia mitovy amin'ny ISBN ho an'ny **gazetiboky sy gazety**. Eo
amin'ny barcode ao ambadiky ny gazetiboky, dia manomboka amin'ny **977** izy.

Tsy toy ny ISBN, ny ISSN dia mamantatra ny **lohatenin'ny gazetiboky**, fa
tsy laharana manokana: ny laharana rehetra amin'ny gazetiboky iray dia
mizara ISSN mitovy. Noho izany, ny BibliOfelia dia mamorona **notice
tokana** isaky ny gazetiboky, ka ny laharana tsirairay dia manampy
exemplaire aminy. Manoratra gazetiboky toy ny boky ianao, amin'ny fandrafetana
ny barcode 977-ny fotsiny.

### Laharan-karatra / laharana mpianatra

Io no code Ofelia an'ny karatra mpianatra (préfixe 291). Antsoina
hoe "laharan-karatra" na "laharana mpianatra" — mitovy ireo.

## Ireo teny hafa

### BibliOfelia

Ny logiciel fitantanana tranomboky, voa-install amin'ny **Ofelia
Box**. Azo idirana avy amin'ny ordinateur na tablette tsirairay
an'ny tranomboky amin'ny alalan'ny navigateur web.

### Famakiana eo an-toerana

Boky vakiana ao amin'ny tranomboky tsy nampindramina (BD novakiana,
dictionnaire nanontaniana ho an'ny devoir). Azo soratana ho an'ny
statistika. Jereo [Famakiana eo
an-toerana](prets-retours/consultation.md).

### Scanner

Mpamaky code-barre tafiditra amin'ny tariby USB amin'ny ordinateur.
Miasa toy ny clavier: jerena, miseho ao amin'ny toerana fampidirana
ny code. Ny fitaovana haingana indrindra.

### Kopia

Kopia ara-batana an'ny boky. Notice iray dia afaka manana kopia
maromaro (ohatra, kopia 3 an'ny *Le Petit Prince* eo amin'ny
rakitra). Kopia tsirairay manana ny code Ofeliany. Jereo
[Fitantanana kopia](catalogue/exemplaires.md).

### Toerana

Ny rakitra na vatasalaka izay ametrahana ny boky. Hita amin'ny code
fohy (`A1`, `TAN`, `BD`…). Jereo [Toerana](catalogue/localisations.md).

### Mpianatra

Mpamaky voasoratra ao amin'ny tranomboky. Manana karatra misy
laharana miavaka. Antsoina koa hoe **mpampiasa** na **mpamaky**.

### Notice

Ny takelaka mamaritra ny boky (lohateny, mpanoratra, ISBN…). Tsy
miankina amin'ny kopia ara-batana: notice iray dia afaka misy tsy
misy kopia (boky voafaritra fa tsy mbola tonga) na manana kopia
maromaro (boky malaza). Jereo [Manampy
boky](catalogue/ajouter-livre.md).

### Ofelia Box

Ny boîtier kely (mini-ordinateur Raspberry Pi) izay mitazona ny
BibliOfelia. Tafiditra amin'ny réseau an'ny tranomboky, mizara ny
aplikasiona amin'ny ordinateur rehetra tafiditra. Tsy mila internet
mba hiasa.

### OfeliaScan

Ny aplikasiona Android namana an'ny BibliOfelia. Manova ny finday
ho scanner ho an'ny code-barre. Jereo [Hampandeha
OfeliaScan](ofeliascan/activer.md).

### Sazy

Vola faktiorina **tanana** avy amin'ny takelakan'ny mpianatra (antony
+ vola). Tsy kajy ho azy mihitsy ny sazy tara. Jereo
[Caisse sy faktiora](caisse/caisse.md).

### Animation

Fivoriana miaraka amin'ny olona (ora tantara, atelier). Isaina ny
mpianatra tonga (scan na isa 4 farany amin'ny karatra) ary, manokana,
ny tsy mpianatra. Jereo
[Asa sy animation](caisse/activites.md).

### Bouclement

Faran'ny tolotra anio: asa, caisse, fandefasana, backup, ary amin'ny
Box ihany ny famonoana. Jereo
[Famaranana ny andro](caisse/bouclement.md).

### Caisse

Lisitry ny fidirana sy fivoahan'ny vola an-tanana, tsy mitovy amin'ny
virement. Saldo, faktiora, filaharan'ny mailaka. Jereo
[Caisse sy faktiora](caisse/caisse.md).

### Saram-pianarana

Vola isan-taona entin'ny **sokajy mpianatra**, faktiorina ho azy
amin'ny fisoratana sy amin'ny fanavaozana. 0 = maimaim-poana. Jereo
[Saran'ny sokajy mpianatra](caisse/tarifs.md).

### Fampindramana

Ny fampindramana boky amin'ny mpianatra, miaraka amin'ny daty
famerenana. Jereo [Mampindrana boky](prets-retours/faire-pret.md).

### Récolement

Fijerena rakitra: mandalo amin'ny rakitra ary mijery boky tsirairay
mba hanamarinana fa ao amin'ny toerany. Jereo
[Récolement](inventaire/recolement.md).

### Famandrihana

Fangatahana fampindramana ho an'ny boky tsy misy ankehitriny. Ny
mpianatra dia hovaliana voalohany rehefa miverina ny boky. Jereo
[Famandrihana](reservations/creer.md).
