import app.algorithm.country_standardisation as mapper
from app.algorithm.country_standardisation.steps import _standardise_country
from tests.utils import rows_equal_query_results


def test_country_mapping(
    add_datahub_export_to_countries,
    add_datahub_future_interest_countries,
    add_datahub_omis,
    add_export_wins,
    add_country_territory_registry,
):

    add_datahub_export_to_countries(
        [
            {
                'company_id': '25262ffe-e062-49af-a620-a84d4f3feb8b',
                'country_iso_alpha2_code': 'AF',
                'country': 'afganistan',
                'id': 0,
            },
            {
                'company_id': '25262ffe-e062-49af-a620-a84d4f3feb8b',
                'country_iso_alpha2_code': 'AN',
                'country': 'netherlands antilles',
                'id': 1,
            },
        ]
    )

    add_datahub_future_interest_countries(
        [
            {
                'company_id': 'd584c5e2-ef16-4aba-91d4-71949078831f',
                'country_iso_alpha2_code': 'AD',
                'country': 'Andorra',
                'id': 0,
            }
        ]
    )
    add_datahub_omis(
        [
            {
                'company_id': '7ff93060-1f05-4bbc-a58a-65ae7d7e8ba8',
                'created_date': '2009-10-10',
                'datahub_omis_order_id': 'a0e38b4f-f4c9-4ebc-b196-208972268efb',
                'market': 'usa',
                'sector': 'Aerospace',
            }
        ]
    )
    add_export_wins(
        [
            {
                'export_wins_company_id': '12345678',
                'contact_email_address': 'test@testcompany.com',
                'sector': 'Aerospace',
                'compay_name': 'Test Company',
                'country': 'uae',
                'export_win_id': 'ffa75985-7bc0-4e9f-8d58-28a7f234b7fc',
                'created_on': '2009-10-10 12:12:12',
                'date_won': '2010-11-11 12:12:12',
            },
            {
                'export_wins_company_id': '12345678',
                'contact_email_address': 'test@testcompany.com',
                'sector': 'Aerospace',
                'compay_name': 'Company testing',
                'country': 'unknown',
                'export_win_id': 'ffa75985-7bc0-4e9f-8d58-28a7f234b7fc',
                'created_on': '2009-10-10 12:12:12',
                'date_won': '2010-11-11 12:12:12',
            },
        ]
    )

    # Populate registry
    countries = [
        ('AF', 'Afghanistan'),
        ('AL', 'Albania'),
        ('DZ', 'Algeria'),
        ('AD', 'Andorra'),
        ('AO', 'Angola'),
        ('AG', 'Antigua and Barbuda'),
        ('BE', 'Belgium'),
        ('CL', 'Chile'),
        ('FR', 'France'),
        ('NZ', 'New Zealand'),
        ('CA', 'Canada'),
        ('US', 'United States'),
        ('CN', 'China'),
        ('DE', 'Germany'),
        ('BS', 'The Bahamas'),
        ('IN', 'India'),
        ('JP', 'Japan'),
        ('US', 'United States'),
        ('AU', 'Australia'),
        ('NZ', 'New Zealand'),
        ('CA', 'Canada'),
        ('AE', 'United Arab Emirates'),
    ]
    country_territory_entries = []
    for iso_alpha2_code, country in countries:
        entry = {'country_iso_alpha2_code': iso_alpha2_code, 'name': country}
        country_territory_entries.append(entry)
    add_country_territory_registry(country_territory_entries)

    # Standardise
    mapper.standardise_countries()

    # TODO: uncomment once export wins is included
    expected_rows = [
        (1, 'afganistan', 'Afghanistan', 91),
        (2, 'Andorra', 'Andorra', 100),
        (3, 'netherlands antilles', 'Bonaire', 100),
        (4, 'netherlands antilles', 'Saint Eustatius', 100),
        (5, 'netherlands antilles', 'Saba', 100),
        (6, 'netherlands antilles', 'Curaçao', 100),
        (7, 'netherlands antilles', 'Sint Maarten (Dutch part)', 100),
        (8, 'usa', 'United States', 100),
    ]
    assert rows_equal_query_results(
        expected_rows, f'SELECT * FROM "{mapper.output_schema}"."{mapper.output_table}"'
    )


def test_standardise_country():

    choices = [
        'Belgium',
        'Austria',
        'South Africa',
        'Germany',
        'The Bahamas',
        'United Arab Emirates',
        'United States',
        'Congo (Democratic Republic)',
        'Laos',
        'Central African Replublic',
        'Netherlands Antilles',
    ]
    lower_choices = [choice.lower() for choice in choices]

    # test sensible matches (threshold > 85)
    assert _standardise_country('Belgium', choices, lower_choices) == [('Belgium', 100)]
    assert _standardise_country('South Africa', choices, lower_choices) == [
        ('South Africa', 100)
    ]
    assert _standardise_country('uae', choices, lower_choices) == [
        ('United Arab Emirates', 100)
    ]
    assert _standardise_country('usa', choices, lower_choices) == [
        ('United States', 100)
    ]
    assert _standardise_country('Africa Belgium', choices, lower_choices) == [
        ('Belgium', 90)
    ]
    assert _standardise_country('Africa Belgium Austria', choices, lower_choices) == [
        ('Belgium', 90),
        ('Austria', 90),
    ]
    assert _standardise_country('Africa and Belgium', choices, lower_choices) == [
        ('Belgium', 90)
    ]
    assert _standardise_country('german', choices, lower_choices) == [('Germany', 88)]
    assert _standardise_country('Belgiun', choices, lower_choices) == [('Belgium', 86)]
    assert _standardise_country('Belgiu', choices, lower_choices) == [('Belgium', 88)]
    assert _standardise_country(
        'democratic republic of congo', choices, lower_choices
    ) == [('Congo (Democratic Republic)', 91)]
    assert _standardise_country('bahamas', choices, lower_choices) == [
        ('The Bahamas', 90)
    ]
    assert _standardise_country('ao', choices, lower_choices) == [('Laos', 86)]

    # test mismatches
    assert _standardise_country('Africa', choices, lower_choices) == [('Belgium', 0)]
    assert _standardise_country('Unknown', choices, lower_choices) == [
        ('United Arab Emirates', 19)
    ]
    assert _standardise_country('africa (any)', choices, lower_choices) == [
        ('South Africa', 71)
    ]
    assert _standardise_country('a', choices, lower_choices) == [
        ('Austria', 66),
        ('Germany', 66),
        ('Laos', 78),
    ]
    assert _standardise_country('anywhere in the world', choices, lower_choices) == [
        ('The Bahamas', 82)
    ]
    assert _standardise_country(
        'Central African Replublic', choices, lower_choices
    ) == [('Central African Replublic', 100)]
    assert _standardise_country('Netherlands Anilles', choices, lower_choices) == [
        ('Bonaire', 93),
        ('Saint Eustatius', 93),
        ('Saba', 93),
        ('Curaçao', 93),
        ('Sint Maarten (Dutch part)', 93),
    ]
