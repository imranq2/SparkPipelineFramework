from typing import List, Optional

from pyspark.ml.base import Transformer
from pyspark.sql.dataframe import DataFrame

from spark_pipeline_framework.logger.yarn_logger import get_logger
from spark_pipeline_framework.progress_logger.progress_log_metric import ProgressLogMetric
from spark_pipeline_framework.progress_logger.progress_logger import ProgressLogger
from spark_pipeline_framework.utilities.FriendlySparkException import FriendlySparkException
from spark_pipeline_framework.utilities.attr_dict import AttrDict


class FrameworkPipeline(Transformer):
    def __init__(self,
                 parameters: AttrDict,
                 progress_logger: ProgressLogger
                 ):
        super(FrameworkPipeline, self).__init__()
        self.transformers: List[Transformer] = []
        self.parameters: AttrDict = parameters
        self.progress_logger: ProgressLogger = progress_logger

    # noinspection PyUnusedLocal
    def fit(self, df: DataFrame) -> 'FrameworkPipeline':
        return self

    def _transform(self, df: DataFrame) -> DataFrame:
        logger = get_logger(__name__)
        count_of_transformers: int = len(self.transformers)
        i: int = 0
        for transformer in self.transformers:
            stage_name: Optional[str] = None
            try:
                i += 1
                if hasattr(transformer, "getName"):
                    # noinspection Mypy
                    stage_name = transformer.getName()
                    logger.info(f"---- Running transformer {stage_name}  ({i} of {count_of_transformers}) ----")
                    # self.spark_session.sparkContext.setJobDescription(stage_name)
                    # print_memory_stats(sc(df))
                with ProgressLogMetric(progress_logger=self.progress_logger, name=stage_name or "unknown"):
                    df = transformer.transform(dataset=df)
            except Exception as e:
                logger.warn(f"======== stage threw exception =======")
                if hasattr(transformer, "getSql"):
                    # noinspection Mypy
                    logger.info(transformer.getSql())
                logger.warn(f"======== stage threw exception =======")
                # use exception chaining to add stage name but keep original exception
                raise FriendlySparkException(str(e), stage_name=stage_name)
        return df