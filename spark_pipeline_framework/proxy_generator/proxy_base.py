from os import listdir, path
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from pyspark.ml.base import Transformer

from spark_pipeline_framework.progress_logger.progress_logger import ProgressLogger
from spark_pipeline_framework.proxy_generator.python_transformer_helpers import get_python_transformer_from_location, \
    get_python_function_from_location
from spark_pipeline_framework.transformers.framework_csv_loader import FrameworkCsvLoader
from spark_pipeline_framework.transformers.framework_mapping_runner import FrameworkMappingLoader
from spark_pipeline_framework.transformers.framework_sql_transformer import FrameworkSqlTransformer


class ProxyBase:
    loader: Optional[Transformer] = None
    converter: Optional[Transformer] = None
    feature: Optional[Transformer] = None
    location: str = ""

    def __init__(
        self,
        parameters: Dict[str, Any],
        location: Union[str, Path],
        progress_logger: Optional[ProgressLogger] = None,
        verify_count_remains_same: bool = False
    ) -> None:
        self.parameters: Dict[str, Any] = parameters
        self.progress_logger: Optional[ProgressLogger] = progress_logger
        self.verify_count_remains_same: bool = verify_count_remains_same
        self.location: str = str(location)

        assert self.location
        # Iterate over files to create transformers
        files: List[str] = listdir(self.location)
        index_of_module: int = self.location.rfind("/library/")
        module_name: str = self.location[index_of_module +
                                         1:].replace("/", ".")

        for file in files:
            if file == 'my_view.sql':
                load_sql: str = self.read_file_as_string(
                    path.join(self.location, file)
                ).format(parameters=parameters)
                self.loader = FrameworkSqlTransformer(
                    sql=load_sql,
                    name=module_name,
                    progress_logger=progress_logger,
                    log_sql=parameters.get("debug_log_sql", False)
                )
            elif file.endswith('.csv') and self.loader is None:
                file_name = file.replace('.csv', '')
                self.loader = FrameworkCsvLoader(
                    view=file_name,
                    path_to_csv=path.join(self.location, file),
                    delimiter=parameters.get("delimiter", ",")
                )
            elif file == 'convert.sql':
                convert_sql: str = self.read_file_as_string(path.join(self.location, file)) \
                    .format(parameters=parameters)
                self.converter = FrameworkSqlTransformer(
                    sql=convert_sql,
                    name=module_name,
                    progress_logger=progress_logger,
                    log_sql=parameters.get("debug_log_sql", False)
                )
            elif file.endswith(
                '.sql'
            ) and self.loader is None and self.converter is None:
                feature_sql: str = self.read_file_as_string(path.join(self.location, file)) \
                    .format(parameters=parameters)
                self.feature = FrameworkSqlTransformer(
                    sql=feature_sql,
                    name=module_name,
                    progress_logger=progress_logger,
                    log_sql=parameters.get("debug_log_sql", False),
                    view=file.replace('.sql', ''),
                    verify_count_remains_same=verify_count_remains_same
                )
            elif file == 'calculate.py':
                self.feature = self.get_python_transformer('.calculate')
            elif file == 'mapping.py':
                self.feature = self.get_python_mapping_transformer('.mapping')

    @staticmethod
    def read_file_as_string(file_path: str) -> str:
        with open(file_path, 'r') as file:
            file_contents = file.read()
        return file_contents

    @property
    def transformers(self) -> List[Transformer]:
        return [
            transformer
            for transformer in [self.loader, self.converter, self.feature]
            if transformer is not None
        ]

    @transformers.setter
    def transformers(self, value: Any) -> None:
        raise AttributeError("transformers property is read only.")

    def get_python_transformer(self, import_module_name: str) -> Transformer:
        return get_python_transformer_from_location(
            location=self.location,
            import_module_name=import_module_name,
            parameters=self.parameters,
            progress_logger=self.progress_logger
        )

    def get_python_mapping_transformer(
        self, import_module_name: str
    ) -> Transformer:
        return FrameworkMappingLoader(
            view=self.parameters["view"],
            mapping_function=get_python_function_from_location(
                location=self.location, import_module_name=import_module_name
            ),
            parameters=self.parameters,
            progress_logger=self.progress_logger
        )
