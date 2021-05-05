from typing import List, Union

from pyspark.ml import Transformer

from spark_pipeline_framework.transformers.framework_transformer.v1.framework_transformer import (
    FrameworkTransformer,
)
from spark_pipeline_framework.utilities.flattener import flatten


def create_steps(
    my_list: Union[
        List[Transformer], List[FrameworkTransformer], List[List[Transformer]]
    ]
) -> List[Transformer]:
    return flatten(my_list)
