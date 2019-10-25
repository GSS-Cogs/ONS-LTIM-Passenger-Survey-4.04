# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.1.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Migration to and from the United Kingdom by area of destination or origin within the UK by citizenship

# +
from gssutils import *

scraper = Scraper('https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/internationalmigration/datasets/ipsareaofdestinationororiginwithintheukbycitizenship')
# -

scraper

tabs = scraper.distributions[0].as_databaker()


# Each tab is of the same form, with "software readable codes":
#
# > The datasheets can be imported directly into suitable software. When importing the datasheets into other software import only rows 8 to 53, starting at column E.
#
# Actually, the admin geo code is also useful, so we'll start at column D

# +
def citizenship_code(s):
    code = pathify(s)
    assert code.startswith('cit-'), code
    code = code[4:]
    assert code.endswith('-est'), code
    code = code[:-4]
    return code.replace('-/-', '-')

def flow_code(s):
    return pathify(s[:s.find(',')])

tidied_sheets = []

for tab in tabs:
    if not tab.name.startswith('Data'):
        continue
    year = int(tab.excel_ref('A2').value[-4:])

    start = tab.excel_ref('D8')
    end = tab.excel_ref('D53')
    admin_geo = start.fill(DOWN) & end.expand(UP)
    codes = admin_geo.shift(RIGHT)
    observations = codes.fill(RIGHT)
    citizenship = start.shift(RIGHT).fill(RIGHT)
    # sheets B, C and D repeat 'All citizenships', 'British' and 'Stateless' from sheet A
    if not tab.name.endswith('A'):
        citizenship = citizenship - citizenship.regex(r'CIT (All|British|Stateless)')
    citizenship_ci = citizenship.regex(r'.*CI\s*$')
    citizenship_est = citizenship - citizenship_ci
    observations_est = observations & citizenship_est.fill(DOWN)
    observations_ci = observations & citizenship_ci.fill(DOWN)
    cs_est = ConversionSegment(observations_est, [
        HDimConst('Year', year),
        HDim(admin_geo, 'Area of Destination or Origin', DIRECTLY, LEFT),
        HDim(codes, 'Migration Flow', DIRECTLY, LEFT),
        HDim(citizenship_est, 'IPS Citizenship', DIRECTLY, ABOVE),
        HDim(observations_ci, 'CI', DIRECTLY, RIGHT),
        HDimConst('Measure Type', 'Count'),
        HDimConst('Unit', 'people-thousands')
    ])

    savepreviewhtml(cs_est)
    tidy_sheet = cs_est.topandas()
    tidy_sheet['IPS Citizenship'] = tidy_sheet['IPS Citizenship'].apply(citizenship_code)
    tidy_sheet['Migration Flow'] = tidy_sheet['Migration Flow'].apply(flow_code)
    tidy_sheet.rename(columns={'OBS': 'Value', 'DATAMARKER': 'IPS Marker'}, inplace=True)
    tidy_sheet = tidy_sheet[['Year', 'Area of Destination or Origin', 'Migration Flow', 'IPS Citizenship', 'CI',
                             'Value', 'IPS Marker', 'Measure Type', 'Unit']]
    tidied_sheets.append(tidy_sheet)
# -

tidy = pd.concat(tidied_sheets)
tidy['IPS Marker'] = tidy['IPS Marker'].map(
    lambda x : {
    'z': 'not-applicable',
    '.': 'no-contact',
    '0~': 'rounds-to-zero'}.get (x,x))
tidy['CI'] = pd.to_numeric(tidy['CI'], errors='coerce')
out = Path('out')
out.mkdir(exist_ok=True, parents=True)
tidy.to_csv(out / 'observations.csv', index=False)

# +
from gssutils.metadata import THEME

scraper.dataset.family = 'migration'
scraper.dataset.theme = THEME['population']
with open(out / 'dataset.trig', 'wb') as metadata:
    metadata.write(scraper.generate_trig())
# -

csvw = CSVWMetadata('https://gss-cogs.github.io/ref_migration/')
csvw.create(out / 'observations.csv', out / 'observations.csv-schema.json')

tidy['Measure Type']= tidy['Measure Type'].map(pathify)
tidy.to_csv(out / 'observations-alt.csv', index = False)
csvw.create(out / 'observations-alt.csv', out / 'observations-alt.csv-metadata.json', with_transform=True,
            base_url='http://gss-data.org.uk/data/', base_path='gss_data/migration/ons-ltim-passenger-survey-4-01',
            dataset_metadata=scraper.dataset.as_quads())


