#!/usr/bin/env python3
"""ATC (Anatomical Therapeutic Chemical) code reference data.

Provides human-readable names for ATC codes at three levels:
- Level 1: Single letter (A-V, Z for unknown)
- Level 2: 3 characters (e.g., A10, L01)
- Level 3: 4-5 characters (e.g., A10BD, L01FF)

Used by build_ema.py to create the By-ATC hierarchical view.
"""

# Level 1: Anatomical main group (single letter)
ATC_LEVEL1 = {
    'A': 'Alimentary-Metabolism',
    'B': 'Blood',
    'C': 'Cardiovascular',
    'D': 'Dermatologicals',
    'G': 'Genitourinary-Sex-hormones',
    'H': 'Systemic-hormones',
    'J': 'Anti-infectives',
    'L': 'Antineoplastic-Immunomod',
    'M': 'Musculoskeletal',
    'N': 'Nervous-system',
    'P': 'Antiparasitic',
    'R': 'Respiratory',
    'S': 'Sensory-organs',
    'V': 'Various',
    'Z': 'Unknown',  # Catch-all for products without ATC code
}

# Level 2: Therapeutic subgroup (3 characters)
ATC_LEVEL2 = {
    # A - Alimentary tract and metabolism
    'A01': 'Stomatological',
    'A02': 'Acid-disorders',
    'A03': 'Functional-GI-disorders',
    'A04': 'Antiemetics',
    'A05': 'Bile-liver-therapy',
    'A06': 'Laxatives',
    'A07': 'Antidiarrheals',
    'A08': 'Antiobesity',
    'A09': 'Digestives',
    'A10': 'Diabetes',
    'A11': 'Vitamins',
    'A12': 'Mineral-supplements',
    'A13': 'Tonics',
    'A14': 'Anabolic-agents',
    'A15': 'Appetite-stimulants',
    'A16': 'Other-metabolic',

    # B - Blood and blood forming organs
    'B01': 'Antithrombotics',
    'B02': 'Antihemorrhagics',
    'B03': 'Antianemic',
    'B05': 'Blood-substitutes',
    'B06': 'Other-hematological',

    # C - Cardiovascular system
    'C01': 'Cardiac-therapy',
    'C02': 'Antihypertensives',
    'C03': 'Diuretics',
    'C04': 'Peripheral-vasodilators',
    'C05': 'Vasoprotectives',
    'C07': 'Beta-blockers',
    'C08': 'Ca-channel-blockers',
    'C09': 'Renin-angiotensin',
    'C10': 'Lipid-modifying',

    # D - Dermatologicals
    'D01': 'Antifungals-topical',
    'D02': 'Emollients-protectives',
    'D03': 'Wound-healing',
    'D04': 'Antipruritics',
    'D05': 'Antipsoriatics',
    'D06': 'Antibiotics-topical',
    'D07': 'Corticosteroids-topical',
    'D08': 'Antiseptics-disinfectants',
    'D09': 'Medicated-dressings',
    'D10': 'Anti-acne',
    'D11': 'Other-dermatological',

    # G - Genito-urinary system and sex hormones
    'G01': 'Gynecological-antiinfectives',
    'G02': 'Gynecological',
    'G03': 'Sex-hormones',
    'G04': 'Urologicals',

    # H - Systemic hormonal preparations
    'H01': 'Pituitary-hormones',
    'H02': 'Corticosteroids',
    'H03': 'Thyroid-therapy',
    'H04': 'Pancreatic-hormones',
    'H05': 'Calcium-homeostasis',

    # J - Antiinfectives for systemic use
    'J01': 'Antibacterials',
    'J02': 'Antifungals',
    'J04': 'Antimycobacterials',
    'J05': 'Antivirals',
    'J06': 'Immune-sera-Ig',
    'J07': 'Vaccines',

    # L - Antineoplastic and immunomodulating agents
    'L01': 'Antineoplastics',
    'L02': 'Endocrine-therapy',
    'L03': 'Immunostimulants',
    'L04': 'Immunosuppressants',

    # M - Musculo-skeletal system
    'M01': 'Anti-inflammatory',
    'M02': 'Topical-joint-muscle',
    'M03': 'Muscle-relaxants',
    'M04': 'Antigout',
    'M05': 'Bone-diseases',
    'M09': 'Other-musculoskeletal',

    # N - Nervous system
    'N01': 'Anesthetics',
    'N02': 'Analgesics',
    'N03': 'Antiepileptics',
    'N04': 'Anti-parkinson',
    'N05': 'Psycholeptics',
    'N06': 'Psychoanaleptics',
    'N07': 'Other-CNS',

    # P - Antiparasitic products
    'P01': 'Antiprotozoals',
    'P02': 'Anthelmintics',
    'P03': 'Ectoparasiticides',

    # R - Respiratory system
    'R01': 'Nasal-preparations',
    'R02': 'Throat-preparations',
    'R03': 'Obstructive-airway',
    'R05': 'Cough-cold',
    'R06': 'Antihistamines',
    'R07': 'Other-respiratory',

    # S - Sensory organs
    'S01': 'Ophthalmologicals',
    'S02': 'Otologicals',
    'S03': 'Ophthalm-otological',

    # V - Various
    'V01': 'Allergens',
    'V03': 'Other-therapeutics',
    'V04': 'Diagnostics',
    'V06': 'General-nutrients',
    'V07': 'All-other-non-therapeutic',
    'V08': 'Contrast-media',
    'V09': 'Diagnostic-radiopharm',
    'V10': 'Therapeutic-radiopharm',
    'V20': 'Surgical-dressings',

    # Z - Unknown (catch-all)
    'Z00': 'Unknown',
}

# Level 3: Pharmacological/chemical subgroup (4-5 characters)
ATC_LEVEL3 = {
    # A10 - Diabetes
    'A10A': 'Insulins',
    'A10AB': 'Insulins-rapid-acting',
    'A10AC': 'Insulins-intermediate',
    'A10AD': 'Insulins-combinations',
    'A10AE': 'Insulins-long-acting',
    'A10B': 'Blood-glucose-lowering',
    'A10BA': 'Biguanides',
    'A10BB': 'Sulfonylureas',
    'A10BD': 'Oral-combinations',
    'A10BF': 'Alpha-glucosidase-inhibitors',
    'A10BG': 'Thiazolidinediones',
    'A10BH': 'DPP-4-inhibitors',
    'A10BJ': 'GLP-1-analogues',
    'A10BK': 'SGLT2-inhibitors',
    'A10BX': 'Other-diabetes-drugs',

    # A16 - Other metabolic
    'A16AA': 'Amino-acids',
    'A16AB': 'Enzymes',
    'A16AX': 'Other-metabolic-products',

    # B01 - Antithrombotics
    'B01AA': 'Vitamin-K-antagonists',
    'B01AB': 'Heparin-group',
    'B01AC': 'Platelet-aggregation-inhibitors',
    'B01AD': 'Enzymes',
    'B01AE': 'Direct-thrombin-inhibitors',
    'B01AF': 'Direct-factor-Xa-inhibitors',
    'B01AX': 'Other-antithrombotics',

    # B02 - Antihemorrhagics
    'B02AA': 'Amino-acids',
    'B02AB': 'Proteinase-inhibitors',
    'B02BA': 'Vitamin-K',
    'B02BB': 'Fibrinogen',
    'B02BC': 'Local-hemostatics',
    'B02BD': 'Blood-coagulation-factors',
    'B02BX': 'Other-systemic-hemostatics',

    # C09 - Renin-angiotensin
    'C09AA': 'ACE-inhibitors-plain',
    'C09BA': 'ACE-inhibitors-diuretics',
    'C09BB': 'ACE-inhibitors-Ca-blockers',
    'C09CA': 'ARBs-plain',
    'C09DA': 'ARBs-diuretics',
    'C09DB': 'ARBs-Ca-blockers',
    'C09DX': 'ARBs-other-combinations',
    'C09XA': 'Renin-inhibitors',

    # C10 - Lipid modifying
    'C10AA': 'HMG-CoA-reductase-inhibitors',
    'C10AB': 'Fibrates',
    'C10AC': 'Bile-acid-sequestrants',
    'C10AD': 'Nicotinic-acid',
    'C10AX': 'Other-lipid-modifying',
    'C10BA': 'Statin-combinations',
    'C10BX': 'Other-lipid-combinations',

    # J01 - Antibacterials
    'J01AA': 'Tetracyclines',
    'J01BA': 'Amphenicols',
    'J01CA': 'Penicillins-extended',
    'J01CE': 'Beta-lactamase-sensitive-pen',
    'J01CF': 'Beta-lactamase-resistant-pen',
    'J01CR': 'Penicillin-combinations',
    'J01DB': 'First-gen-cephalosporins',
    'J01DC': 'Second-gen-cephalosporins',
    'J01DD': 'Third-gen-cephalosporins',
    'J01DE': 'Fourth-gen-cephalosporins',
    'J01DF': 'Monobactams',
    'J01DH': 'Carbapenems',
    'J01DI': 'Other-cephalosporins',
    'J01EE': 'Sulfonamide-combinations',
    'J01FA': 'Macrolides',
    'J01FF': 'Lincosamides',
    'J01FG': 'Streptogramins',
    'J01GB': 'Other-aminoglycosides',
    'J01MA': 'Fluoroquinolones',
    'J01XA': 'Glycopeptides',
    'J01XB': 'Polymyxins',
    'J01XC': 'Steroid-antibacterials',
    'J01XD': 'Imidazole-derivatives',
    'J01XE': 'Nitrofuran-derivatives',
    'J01XX': 'Other-antibacterials',

    # J05 - Antivirals
    'J05AB': 'Nucleosides-herpes',
    'J05AC': 'Cyclic-amines',
    'J05AD': 'Phosphonic-acid-derivatives',
    'J05AE': 'Protease-inhibitors',
    'J05AF': 'Nucleoside-RT-inhibitors',
    'J05AG': 'Non-nucleoside-RT-inhibitors',
    'J05AH': 'Neuraminidase-inhibitors',
    'J05AJ': 'Integrase-inhibitors',
    'J05AP': 'HCV-antivirals',
    'J05AR': 'HIV-combinations',
    'J05AX': 'Other-antivirals',

    # J07 - Vaccines
    'J07AC': 'Anthrax-vaccines',
    'J07AD': 'Brucellosis-vaccines',
    'J07AE': 'Cholera-vaccines',
    'J07AF': 'Diphtheria-vaccines',
    'J07AG': 'Hib-vaccines',
    'J07AH': 'Meningococcal-vaccines',
    'J07AJ': 'Pertussis-vaccines',
    'J07AK': 'Plague-vaccines',
    'J07AL': 'Pneumococcal-vaccines',
    'J07AM': 'Tetanus-vaccines',
    'J07AN': 'Tuberculosis-vaccines',
    'J07AP': 'Typhoid-vaccines',
    'J07AR': 'Typhus-vaccines',
    'J07AX': 'Other-bacterial-vaccines',
    'J07BA': 'Encephalitis-vaccines',
    'J07BB': 'Influenza-vaccines',
    'J07BC': 'Hepatitis-vaccines',
    'J07BD': 'Measles-vaccines',
    'J07BE': 'Mumps-vaccines',
    'J07BF': 'Polio-vaccines',
    'J07BG': 'Rabies-vaccines',
    'J07BH': 'Rotavirus-vaccines',
    'J07BJ': 'Rubella-vaccines',
    'J07BK': 'Varicella-vaccines',
    'J07BL': 'Yellow-fever-vaccines',
    'J07BM': 'HPV-vaccines',
    'J07BN': 'COVID-19-vaccines',
    'J07BX': 'Other-viral-vaccines',
    'J07CA': 'Combination-vaccines',
    'J07XA': 'Parasite-vaccines',

    # L01 - Antineoplastics
    'L01A': 'Alkylating-agents',
    'L01AA': 'Nitrogen-mustard-analogues',
    'L01AB': 'Alkyl-sulfonates',
    'L01AC': 'Ethylene-imines',
    'L01AD': 'Nitrosoureas',
    'L01AX': 'Other-alkylating-agents',
    'L01B': 'Antimetabolites',
    'L01BA': 'Folic-acid-analogues',
    'L01BB': 'Purine-analogues',
    'L01BC': 'Pyrimidine-analogues',
    'L01C': 'Plant-alkaloids',
    'L01CA': 'Vinca-alkaloids',
    'L01CB': 'Podophyllotoxin-derivatives',
    'L01CD': 'Taxanes',
    'L01CE': 'Topoisomerase-1-inhibitors',
    'L01CX': 'Other-plant-alkaloids',
    'L01D': 'Cytotoxic-antibiotics',
    'L01DA': 'Actinomycines',
    'L01DB': 'Anthracyclines',
    'L01DC': 'Other-cytotoxic-antibiotics',
    'L01E': 'Protein-kinase-inhibitors',
    'L01EA': 'BCR-ABL-kinase-inhibitors',
    'L01EB': 'EGFR-kinase-inhibitors',
    'L01EC': 'BRAF-kinase-inhibitors',
    'L01ED': 'ALK-kinase-inhibitors',
    'L01EE': 'MEK-inhibitors',
    'L01EF': 'CDK-inhibitors',
    'L01EG': 'mTOR-kinase-inhibitors',
    'L01EH': 'HER2-kinase-inhibitors',
    'L01EJ': 'JAK-inhibitors',
    'L01EK': 'VEGFR-kinase-inhibitors',
    'L01EL': 'Bruton-kinase-inhibitors',
    'L01EM': 'PI3K-inhibitors',
    'L01EN': 'FLT3-inhibitors',
    'L01EO': 'FGFR-inhibitors',
    'L01EP': 'RET-inhibitors',
    'L01EX': 'Other-kinase-inhibitors',
    'L01F': 'Monoclonal-antibodies',
    'L01FA': 'CD20-mAbs',
    'L01FB': 'CD22-mAbs',
    'L01FC': 'CD38-mAbs',
    'L01FD': 'HER2-mAbs',
    'L01FE': 'EGFR-mAbs',
    'L01FF': 'PD-1-PD-L1-inhibitors',
    'L01FG': 'CTLA-4-inhibitors',
    'L01FX': 'Other-mAbs',
    'L01X': 'Other-antineoplastics',
    'L01XA': 'Platinum-compounds',
    'L01XB': 'Methylhydrazines',
    'L01XC': 'Monoclonal-antibiotics-old',
    'L01XD': 'Photodynamic-sensitizers',
    'L01XE': 'Kinase-inhibitors-old',
    'L01XF': 'Retinoids-cancer',
    'L01XG': 'Proteasome-inhibitors',
    'L01XH': 'HDAC-inhibitors',
    'L01XJ': 'Hedgehog-inhibitors',
    'L01XK': 'BCL-2-inhibitors',
    'L01XL': 'Cell-therapies',
    'L01XN': 'SMO-inhibitors',
    'L01XX': 'Other-antineoplastics',
    'L01XY': 'Combinations',

    # L02 - Endocrine therapy
    'L02AA': 'Estrogens',
    'L02AB': 'Progestogens',
    'L02AE': 'GnRH-analogues',
    'L02BA': 'Anti-estrogens',
    'L02BB': 'Anti-androgens',
    'L02BG': 'Aromatase-inhibitors',
    'L02BX': 'Other-hormone-antagonists',

    # L03 - Immunostimulants
    'L03AA': 'Colony-stimulating-factors',
    'L03AB': 'Interferons',
    'L03AC': 'Interleukins',
    'L03AX': 'Other-immunostimulants',

    # L04 - Immunosuppressants
    'L04AA': 'Selective-immunosuppressants',
    'L04AB': 'TNF-alpha-inhibitors',
    'L04AC': 'Interleukin-inhibitors',
    'L04AD': 'Calcineurin-inhibitors',
    'L04AE': 'S1P-receptor-modulators',
    'L04AF': 'IMPDH-inhibitors',
    'L04AG': 'Cell-adhesion-inhibitors',
    'L04AH': 'IL-6-inhibitors',
    'L04AJ': 'IL-23-inhibitors',
    'L04AK': 'IL-17-inhibitors',
    'L04AL': 'FcRn-inhibitors',
    'L04AX': 'Other-immunosuppressants',

    # M05 - Bone diseases
    'M05BA': 'Bisphosphonates',
    'M05BB': 'Bisphosphonate-combinations',
    'M05BC': 'Bone-morphogenetic-proteins',
    'M05BX': 'Other-bone-drugs',

    # N02 - Analgesics
    'N02A': 'Opioids',
    'N02AA': 'Natural-opium-alkaloids',
    'N02AB': 'Phenylpiperidine-derivatives',
    'N02AE': 'Oripavine-derivatives',
    'N02AF': 'Morphinan-derivatives',
    'N02AG': 'Opioid-combinations',
    'N02AJ': 'Opioid-non-opioid-combos',
    'N02AX': 'Other-opioids',
    'N02B': 'Other-analgesics',
    'N02BA': 'Salicylic-acid-derivatives',
    'N02BB': 'Pyrazolones',
    'N02BE': 'Anilides',
    'N02BG': 'Other-analgesics-antipyretics',
    'N02C': 'Antimigraine',
    'N02CA': 'Ergot-alkaloids',
    'N02CB': 'Corticosteroid-derivatives',
    'N02CC': 'Triptans',
    'N02CD': 'CGRP-antagonists',
    'N02CX': 'Other-antimigraine',

    # N03 - Antiepileptics
    'N03AA': 'Barbiturates',
    'N03AB': 'Hydantoin-derivatives',
    'N03AD': 'Succinimide-derivatives',
    'N03AE': 'Benzodiazepine-derivatives',
    'N03AF': 'Carboxamide-derivatives',
    'N03AG': 'Fatty-acid-derivatives',
    'N03AX': 'Other-antiepileptics',

    # N04 - Anti-parkinson
    'N04AA': 'Tertiary-amines',
    'N04AB': 'Ethers-tropine',
    'N04AC': 'Ethers-diphenylmethane',
    'N04BA': 'Dopa-preparations',
    'N04BB': 'Adamantane-derivatives',
    'N04BC': 'Dopamine-agonists',
    'N04BD': 'MAO-B-inhibitors',
    'N04BX': 'Other-dopaminergics',

    # N05 - Psycholeptics
    'N05A': 'Antipsychotics',
    'N05AA': 'Phenothiazines-aliphatic',
    'N05AB': 'Phenothiazines-piperazine',
    'N05AC': 'Phenothiazines-piperidine',
    'N05AD': 'Butyrophenone-derivatives',
    'N05AE': 'Indole-derivatives',
    'N05AF': 'Thioxanthene-derivatives',
    'N05AG': 'Diphenylbutylpiperidine',
    'N05AH': 'Diazepines-oxazepines',
    'N05AL': 'Benzamides',
    'N05AN': 'Lithium',
    'N05AX': 'Other-antipsychotics',
    'N05B': 'Anxiolytics',
    'N05BA': 'Benzodiazepines',
    'N05BB': 'Diphenylmethane-derivatives',
    'N05BC': 'Carbamates',
    'N05BD': 'Dibenzo-bicyclo-octadiene',
    'N05BE': 'Azaspirodecanedione',
    'N05BX': 'Other-anxiolytics',
    'N05C': 'Hypnotics-sedatives',
    'N05CA': 'Barbiturates-plain',
    'N05CB': 'Barbiturates-combinations',
    'N05CC': 'Aldehydes',
    'N05CD': 'Benzodiazepines',
    'N05CE': 'Piperidinedione-derivatives',
    'N05CF': 'Benzodiazepine-related',
    'N05CH': 'Melatonin-receptor-agonists',
    'N05CM': 'Other-hypnotics',
    'N05CX': 'Hypnotics-combinations',

    # N06 - Psychoanaleptics
    'N06A': 'Antidepressants',
    'N06AA': 'Non-selective-MAO-inhibitors',
    'N06AB': 'SSRIs',
    'N06AF': 'MAO-inhibitors-nonselective',
    'N06AG': 'MAO-A-inhibitors',
    'N06AX': 'Other-antidepressants',
    'N06B': 'Psychostimulants-ADHD',
    'N06BA': 'Centrally-acting-sympathomimetics',
    'N06BC': 'Xanthine-derivatives',
    'N06BX': 'Other-psychostimulants',
    'N06D': 'Anti-dementia',
    'N06DA': 'Anticholinesterases',
    'N06DX': 'Other-anti-dementia',

    # N07 - Other CNS
    'N07AA': 'Anticholinesterases',
    'N07AB': 'Parasympathomimetics',
    'N07AX': 'Other-parasympathomimetics',
    'N07BA': 'Nicotine-dependence',
    'N07BB': 'Alcohol-dependence',
    'N07BC': 'Opioid-dependence',
    'N07CA': 'Antivertigo',
    'N07XX': 'Other-nervous-system',

    # R03 - Obstructive airway
    'R03A': 'Adrenergics-inhalants',
    'R03AC': 'Selective-beta-2-agonists',
    'R03AK': 'Adrenergics-corticosteroid-combos',
    'R03AL': 'Adrenergics-anticholinergic-combos',
    'R03B': 'Other-inhalants',
    'R03BA': 'Glucocorticoids',
    'R03BB': 'Anticholinergics',
    'R03BC': 'Antiallergic-excl-corticosteroids',
    'R03BX': 'Other-inhalants',
    'R03C': 'Adrenergics-systemic',
    'R03CC': 'Selective-beta-2-systemic',
    'R03D': 'Other-systemic-obstructive-airway',
    'R03DA': 'Xanthines',
    'R03DC': 'Leukotriene-antagonists',
    'R03DX': 'Other-systemic-asthma',

    # S01 - Ophthalmologicals
    'S01A': 'Antiinfectives-eye',
    'S01AA': 'Antibiotics',
    'S01AB': 'Sulfonamides',
    'S01AD': 'Antivirals',
    'S01AE': 'Fluoroquinolones',
    'S01AX': 'Other-antiinfectives',
    'S01B': 'Antiinflammatory-eye',
    'S01BA': 'Corticosteroids-plain',
    'S01BB': 'Corticosteroids-mydriatics',
    'S01BC': 'Antiinflammatory-non-steroids',
    'S01C': 'Antiinflammatory-antiinfective-combos',
    'S01CA': 'Corticosteroid-antiinfective-combos',
    'S01CB': 'Corticosteroid-antiinfective-mydriatic',
    'S01E': 'Antiglaucoma-miotics',
    'S01EA': 'Sympathomimetics-glaucoma',
    'S01EB': 'Parasympathomimetics',
    'S01EC': 'Carbonic-anhydrase-inhibitors',
    'S01ED': 'Beta-blockers',
    'S01EE': 'Prostaglandin-analogues',
    'S01EX': 'Other-antiglaucoma',
    'S01F': 'Mydriatics-cycloplegics',
    'S01FA': 'Anticholinergics',
    'S01FB': 'Sympathomimetics-mydriatics',
    'S01G': 'Decongestants-antiallergics',
    'S01GA': 'Sympathomimetics-decongestants',
    'S01GX': 'Other-antiallergics',
    'S01H': 'Local-anesthetics',
    'S01HA': 'Local-anesthetics',
    'S01J': 'Diagnostic-agents',
    'S01JA': 'Colouring-agents',
    'S01K': 'Surgical-aids',
    'S01KA': 'Viscoelastic-substances',
    'S01KX': 'Other-surgical-aids',
    'S01L': 'Ocular-vascular-disorder',
    'S01LA': 'Antineovascularization',
    'S01X': 'Other-ophthalmologicals',
    'S01XA': 'Other-ophthalmologicals',

    # V - Various
    'V03AB': 'Antidotes',
    'V03AC': 'Iron-chelating',
    'V03AE': 'Hyperkalemia-hyperphosphatemia',
    'V03AF': 'Detoxifying-antineoplastic',
    'V03AG': 'Hypoglycemia-treatment',
    'V03AH': 'Antidotes-opioid',
    'V03AK': 'Tissue-adhesives',
    'V03AN': 'Medical-gases',
    'V03AX': 'Other-therapeutic',
    'V04CA': 'Diabetes-tests',
    'V04CD': 'Pituitary-tests',
    'V04CF': 'Tuberculosis-diagnostics',
    'V04CG': 'Gastric-secretion-tests',
    'V04CH': 'Kidney-function-tests',
    'V04CJ': 'Fertility-tests',
    'V04CK': 'Liver-function-tests',
    'V04CL': 'Circulation-tests',
    'V04CM': 'Skin-tests-allergens',
    'V04CX': 'Other-diagnostics',
    'V08A': 'X-ray-contrast-iodinated',
    'V08AB': 'Water-soluble-nephrotropic-low-osm',
    'V08B': 'X-ray-contrast-non-iodinated',
    'V08BA': 'Barium-sulfate',
    'V08C': 'MRI-contrast',
    'V08CA': 'Paramagnetic-contrast',
    'V08CB': 'Superparamagnetic-contrast',
    'V08D': 'Ultrasound-contrast',
    'V08DA': 'Ultrasound-contrast',
    'V09A': 'CNS-radiopharm',
    'V09B': 'Skeleton-radiopharm',
    'V09C': 'Kidney-radiopharm',
    'V09D': 'Liver-spleen-radiopharm',
    'V09E': 'Respiratory-radiopharm',
    'V09F': 'Thyroid-radiopharm',
    'V09G': 'Cardiovascular-radiopharm',
    'V09H': 'Inflammation-radiopharm',
    'V09I': 'Tumour-detection-radiopharm',
    'V09X': 'Other-diagnostic-radiopharm',
    'V10A': 'Antiinflammatory-radiopharm',
    'V10B': 'Pain-palliation-radiopharm',
    'V10X': 'Other-therapeutic-radiopharm',

    # Z - Unknown (catch-all)
    'Z00': 'Unknown',
}


def get_atc_name(code: str) -> str | None:
    """Get the human-readable name for an ATC code at any level.

    Args:
        code: ATC code (1-5 characters)

    Returns:
        Human-readable name or None if not found
    """
    code = code.upper()

    # Try level 3 (4-5 chars) first
    if len(code) >= 4:
        if code[:5] in ATC_LEVEL3:
            return ATC_LEVEL3[code[:5]]
        if code[:4] in ATC_LEVEL3:
            return ATC_LEVEL3[code[:4]]

    # Try level 2 (3 chars)
    if len(code) >= 3 and code[:3] in ATC_LEVEL2:
        return ATC_LEVEL2[code[:3]]

    # Try level 1 (1 char)
    if len(code) >= 1 and code[0] in ATC_LEVEL1:
        return ATC_LEVEL1[code[0]]

    return None


def get_atc_hierarchy(code: str) -> list[str]:
    """Get the ATC hierarchy path for a code.

    Args:
        code: ATC code (any length)

    Returns:
        List of folder names for the hierarchy path.
        Each is formatted as "{code} - {name}".
        Returns only distinct levels (no duplicates).
        Uses "Z - Unknown" for missing/invalid codes.
    """
    if not code:
        return ["Z - Unknown"]

    code = code.upper()
    levels = []

    # Level 1: single letter
    l1_code = code[0] if code else 'Z'
    l1_name = ATC_LEVEL1.get(l1_code, 'Unknown')
    level1 = f"{l1_code}) {l1_name}"
    levels.append(level1)

    # Level 2: 3 characters
    if len(code) >= 3:
        l2_code = code[:3]
        l2_name = ATC_LEVEL2.get(l2_code)
        if l2_name:
            level2 = f"{l2_code}) {l2_name}"
            levels.append(level2)

    # Level 3: 4-5 characters
    l3_code = None
    l3_name = None

    # Try 5-char first, then 4-char
    if len(code) >= 5 and code[:5] in ATC_LEVEL3:
        l3_code = code[:5]
        l3_name = ATC_LEVEL3[l3_code]
    elif len(code) >= 4 and code[:4] in ATC_LEVEL3:
        l3_code = code[:4]
        l3_name = ATC_LEVEL3[l3_code]
    elif len(code) >= 4:
        # Use the code even if we don't have a name for it
        l3_code = code[:5] if len(code) >= 5 else code[:4]
        # Try to get a name from the partial code
        l3_name = ATC_LEVEL3.get(l3_code) or ATC_LEVEL3.get(code[:4])

    if l3_code and l3_name:
        level3 = f"{l3_code}) {l3_name}"
        levels.append(level3)

    return levels


if __name__ == "__main__":
    # Test the functions
    test_codes = ["L01FF", "A10BD", "J05AR", "N05AH", "Z", "", "L01XY99", "L01", "B01"]

    for code in test_codes:
        name = get_atc_name(code)
        hierarchy = get_atc_hierarchy(code)
        print(f"{code or '(empty)'}: {name}")
        print(f"  Hierarchy ({len(hierarchy)} levels): {' / '.join(hierarchy)}")
        print()
