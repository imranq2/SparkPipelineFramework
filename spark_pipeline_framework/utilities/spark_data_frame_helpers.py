from collections import OrderedDict
from typing import Dict, Any, List, Optional, Union, cast

# noinspection PyProtectedMember
from pyspark import SparkContext, SQLContext, Row
from pyspark.rdd import RDD
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, DataType, AtomicType


def convert_to_row(d: Dict[Any, Any]) -> Row:
    return Row(**OrderedDict(sorted(d.items())))


def create_view_from_dictionary(
    view: str,
    data: List[Dict[str, Any]],
    spark_session: SparkSession,
    schema: Optional[Union[DataType, str]] = None,
) -> DataFrame:
    """
    parses the dictionary and converts it to a dataframe and creates a view
    :param view:
    :param data:
    :param spark_session:
    :param schema:
    :return: new data frame
    """
    df: DataFrame = create_dataframe_from_dictionary(
        data=data, spark_session=spark_session, schema=schema
    )
    df.createOrReplaceTempView(name=view)
    return df


def create_dataframe_from_dictionary(
    data: List[Dict[str, Any]],
    spark_session: SparkSession,
    schema: Optional[Union[DataType, str]] = None,
) -> DataFrame:
    """
    Creates data frame from dictionary
    :param data:
    :param spark_session:
    :param schema:
    :return: data frame
    """
    rdd: RDD[Any] = spark_session.sparkContext.parallelize(data).map(convert_to_row)
    df: DataFrame = spark_session.createDataFrame(
        data=rdd, schema=cast(AtomicType, schema)
    )
    return df


def create_empty_dataframe(spark_session: SparkSession) -> DataFrame:
    schema = StructType([])

    df: DataFrame = spark_session.createDataFrame(
        spark_session.sparkContext.emptyRDD(), schema
    )

    return df


def create_dataframe_from_json(
    spark_session: SparkSession, schema: StructType, json: str
) -> DataFrame:
    return spark_session.read.schema(schema).json(
        spark_session.sparkContext.parallelize([json])
    )


def spark_is_data_frame_empty(df: DataFrame) -> bool:
    """
    Efficient way to check if the data frame is empty without getting the count of the whole data frame
    """
    # from: https://stackoverflow.com/questions/32707620/how-to-check-if-spark-dataframe-is-empty
    return not bool(df.head(1))


def spark_get_execution_plan(df: DataFrame, extended: bool = False) -> Any:
    if extended:
        # noinspection PyProtectedMember
        return df._jdf.queryExecution().toString()  # type: ignore
    else:
        # noinspection PyProtectedMember
        return df._jdf.queryExecution().simpleString()  # type: ignore


def spark_table_exists(sql_ctx: SQLContext, view: str) -> bool:
    # noinspection PyBroadException
    return view in sql_ctx.tableNames()


def sc(df: DataFrame) -> SparkContext:
    # noinspection PyProtectedMember
    return cast(SparkContext, df._sc)


def add_metadata_to_column(df: DataFrame, column: str, metadata: Any) -> DataFrame:
    return df.withColumn(column, df[column].alias(column, metadata=metadata))


def get_metadata_of_column(df: DataFrame, column: str) -> Any:
    return df.select(column).schema[0].metadata


def to_dicts(df: DataFrame, limit: int) -> List[Dict[str, Any]]:
    """
    converts a data frame into a list of dictionaries
    :param df:
    :param limit:
    :return:
    """
    row: Row
    rows = [row.asDict(recursive=True) for row in df.limit(limit).collect()]
    return rows
