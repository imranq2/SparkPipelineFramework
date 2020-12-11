from typing import Dict, Any, Optional, List, Union

# noinspection PyProtectedMember
from pyspark import keyword_only

# noinspection PyUnresolvedReferences
from pyspark.sql.functions import col
from pyspark.ml.param import Param
from pyspark.sql.dataframe import DataFrame
from spark_pipeline_framework.logger.yarn_logger import get_logger
from spark_pipeline_framework.progress_logger.progress_logger import ProgressLogger
from spark_pipeline_framework.transformers.framework_transformer.v1.framework_transformer import (
    FrameworkTransformer,
)


class FrameworkFilterByColumnTransformer(FrameworkTransformer):
    # noinspection PyUnusedLocal
    @keyword_only
    def __init__(
        self,
        # add your parameters here (be sure to add them to setParams below too)
        column: str,
        include_only: List[Union[str, int, float]],
        view: str,
        name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        progress_logger: Optional[ProgressLogger] = None,
    ):
        super().__init__(
            name=name, parameters=parameters, progress_logger=progress_logger
        )

        self.logger = get_logger(__name__)

        assert column
        self.column: Param = Param(self, "column", "")
        self._setDefault(column=column)

        assert view
        self.view: Param = Param(self, "view", "")
        self._setDefault(view=view)

        assert include_only and isinstance(include_only, list)
        self.include_only: Param = Param(self, "include_only", "")
        self._setDefault(include_only=include_only)

        kwargs = self._input_kwargs
        self.setParams(**kwargs)

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring, PyUnusedLocal
    @keyword_only
    def setParams(
        self,
        # add your parameters here
        column: str,
        include_only: List[Union[str, int, float]],
        view: str,
        name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        progress_logger: Optional[ProgressLogger] = None,
    ) -> Any:
        kwargs = self._input_kwargs
        super().setParams(
            name=name, parameters=parameters, progress_logger=progress_logger
        )
        return self._set(**kwargs)

    def _transform(self, df: DataFrame) -> DataFrame:
        view: str = self.getView()
        column: str = self.getColumn()
        include_only: List[Union[str, int, float]] = self.getIncludeOnly()

        result_df: DataFrame = df.sql_ctx.table(view)
        result_df = result_df.where(col(column).isin(include_only))
        result_df.createOrReplaceTempView(view)

        return df

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getView(self) -> str:
        return self.getOrDefault(self.view)  # type: ignore

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getColumn(self) -> str:
        return self.getOrDefault(self.column)  # type: ignore

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getIncludeOnly(self) -> List[Union[str, int, float]]:
        return self.getOrDefault(self.include_only)  # type: ignore
