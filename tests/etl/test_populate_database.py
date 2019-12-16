import datetime
from unittest.mock import patch

from app.db.db_utils import execute_query, execute_statement
from app.etl.tasks.core import populate_database


@patch('app.etl.tasks.core.extract_datahub_company_dataset')
@patch('app.etl.tasks.core.extract_datahub_export_countries')
@patch('app.etl.tasks.core.extract_datahub_future_interest_countries')
@patch('app.etl.tasks.core.extract_datahub_interactions')
@patch('app.etl.tasks.core.extract_datahub_omis_dataset')
@patch('app.etl.tasks.core.extract_datahub_sectors')
@patch('app.etl.tasks.core.extract_export_wins')
@patch('app.etl.tasks.core.ExportCountriesTask')
@patch('app.etl.tasks.core.PopulateCountriesAndSectorsOfInterestTask')
@patch('app.etl.tasks.core.PopulateCountriesOfInterestTask')
@patch('app.etl.tasks.core.SectorsOfInterestTask')
class TestPopulateDatabase:
    @patch('app.etl.tasks.core.execute_statement')
    def test_tasks_are_run(
        self,
        execute_statement,
        SectorsOfInterestTask,
        PopulateCountriesOfInterestTask,
        PopulateCountriesAndSectorsOfInterestTask,
        ExportCountriesTask,
        extract_export_wins,
        extract_datahub_sectors,
        extract_datahub_omis_dataset,
        extract_datahub_interactions,
        extract_datahub_future_interest_countries,
        extract_datahub_export_countries,
        extract_datahub_company_dataset,
    ):
        output = populate_database(drop_table=True)

        extract_datahub_company_dataset.assert_called_once()
        extract_datahub_export_countries.assert_called_once()
        extract_datahub_future_interest_countries.assert_called_once()
        extract_datahub_interactions.assert_called_once()
        extract_datahub_omis_dataset.assert_called_once()
        extract_datahub_sectors.assert_called_once()
        extract_export_wins.assert_called_once()
        ExportCountriesTask.assert_called_once_with(drop_table=True)
        ExportCountriesTask.return_value.assert_called_once()
        PopulateCountriesAndSectorsOfInterestTask.assert_called_once_with(
            drop_table=True
        )
        (PopulateCountriesAndSectorsOfInterestTask.return_value.assert_called_once())
        PopulateCountriesOfInterestTask.assert_called_once_with(drop_table=True)
        PopulateCountriesOfInterestTask.return_value.assert_called_once()
        SectorsOfInterestTask.assert_called_once_with(drop_table=True)
        SectorsOfInterestTask.return_value.assert_called_once()

        expected_output = {
            'output': [
                extract_datahub_company_dataset.return_value,
                extract_datahub_export_countries.return_value,
                extract_datahub_interactions.return_value,
                extract_datahub_future_interest_countries.return_value,
                extract_datahub_omis_dataset.return_value,
                extract_datahub_sectors.return_value,
                extract_export_wins.return_value,
                ExportCountriesTask.return_value.return_value,
                (PopulateCountriesAndSectorsOfInterestTask.return_value.return_value),
                PopulateCountriesOfInterestTask.return_value.return_value,
                SectorsOfInterestTask.return_value.return_value,
            ]
        }

        assert output == expected_output

    @patch('app.etl.tasks.core.datetime')
    def test_updates_task_status_to_success(
        self,
        mock_datetime,
        SectorsOfInterestTask,
        PopulateCountriesOfInterestTask,
        PopulateCountriesAndSectorsOfInterestTask,
        ExportCountriesTask,
        extract_export_wins,
        extract_datahub_sectors,
        extract_datahub_omis_dataset,
        extract_datahub_interactions,
        extract_datahub_future_interest_countries,
        extract_datahub_export_countries,
        extract_datahub_company_dataset,
        app_with_db,
    ):
        mock_datetime.datetime.now.return_value = datetime.datetime(2019, 1, 1, 2)
        sql = (
            'create table if not exists etl_status ('
            'status varchar(100), timestamp timestamp)'
        )
        execute_statement(sql)
        sql = "insert into etl_status values" "('RUNNING', '2019-01-01 01:00')"
        execute_statement(sql)
        populate_database(drop_table=True)
        sql = 'select * from etl_status'
        rows = execute_query(sql, df=False)
        assert len(rows) == 1
        assert rows == [('SUCCESS', datetime.datetime(2019, 1, 1, 2))]