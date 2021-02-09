from typing import Dict, Any, Optional

# noinspection PyProtectedMember
from pyspark import keyword_only
from pyspark.ml.param import Param
from pyspark.sql.dataframe import DataFrame
from spark_pipeline_framework.logger.yarn_logger import get_logger
from spark_pipeline_framework.progress_logger.progress_logger import ProgressLogger
from spark_pipeline_framework.transformers.framework_transformer.v1.framework_transformer import (
    FrameworkTransformer,
)


class FrameworkJdbcReader(FrameworkTransformer):
    # noinspection PyUnusedLocal
    @keyword_only
    def __init__(
        self,
        # add your parameters here (be sure to add them to setParams below too)
        jdbc_url: str,
        query: str,
        driver: str,
        view: Optional[str] = None,
        name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        progress_logger: Optional[ProgressLogger] = None,
    ):
        super().__init__(
            name=name, parameters=parameters, progress_logger=progress_logger
        )
        assert jdbc_url
        assert query
        assert driver

        self.logger = get_logger(__name__)

        # add a param
        self.jdbc_url: Param = Param(self, "jdbc_url", "")
        self._setDefault(jdbc_url=jdbc_url)

        self.query: Param = Param(self, "query", "")
        self._setDefault(query=query)

        self.driver: Param = Param(self, "driver", "")
        self._setDefault(driver=driver)

        self.view: Param = Param(self, "view", "")
        self._setDefault(view=view)

        kwargs = self._input_kwargs
        self.setParams(**kwargs)

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring, PyUnusedLocal
    @keyword_only
    def setParams(
        self,
        # add your parameters here
        jdbc_url: str,
        query: str,
        driver: str,
        view: Optional[str] = None,
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
        # pushdown_query = "(select * from employees where emp_no < 10008) emp_alias"
        query: str = self.getQuery()
        jdbc_url: str = self.getJdbcUrl()
        driver: str = self.getDriver()
        view: Optional[str] = self.getView()
        df = (
            df.sql_ctx.read.format("jdbc")
            .option("url", jdbc_url)
            .option(
                "table", query
            )  # passing "(sql query) table_alias" into "table" parameter.
            .option("driver", driver)
            .load()
        )

        if view:
            df.createOrReplaceTempView(view)

        return df

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getJdbcUrl(self) -> str:
        return self.getOrDefault(self.jdbc_url)  # type: ignore

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getDriver(self) -> str:
        return self.getOrDefault(self.driver)  # type: ignore

    def getFormat(self) -> str:
        return "jdbc"

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getQuery(self) -> str:
        return self.getOrDefault(self.query)  # type: ignore

    # noinspection PyPep8Naming,PyMissingOrEmptyDocstring
    def getView(self) -> Optional[str]:
        return self.getOrDefault(self.view)  # type: ignore
