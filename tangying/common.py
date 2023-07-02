from sqlalchemy import create_engine
from tangying import settings
import akshare as ak
import pandas as pd

def initSqliteEngine():
    global sqlite_engine
    database_name = settings.DATABASES['default']['NAME']
    database_url = 'sqlite:///{database_name}'.format(database_name=database_name)
    sqlite_engine = create_engine(database_url,echo=False)

def getSqliteEngine():
    return sqlite_engine

def initBasicData():
    # stock_sh_a_spot_em_df = ak.stock_sh_a_spot_em()[['代码','名称']]
    # stock_sz_a_spot_em_df = ak.stock_sz_a_spot_em()[['代码','名称']]
    stock_a_spot_em_df = pd.concat([ak.stock_sh_a_spot_em()[['代码','名称']],ak.stock_sz_a_spot_em()[['代码','名称']]])
    stock_a_spot_em_df.rename(columns={'代码':'code','名称':'value'},inplace=True)
    stock_a_spot_em_df.reset_index(drop=True)

    stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()[['概念名称','代码']]
    stock_board_concept_name_ths_df.rename(columns={'概念名称':'name','代码':'code'},inplace=True)
    stock_board_industry_name_ths_df = ak.stock_board_industry_name_ths()
    stock_board_name_ths_df = pd.concat([stock_board_concept_name_ths_df,stock_board_industry_name_ths_df])
    stock_board_name_ths_df.drop_duplicates(subset=['code'],inplace=True)

    engine = getSqliteEngine()
    stock_board_name_ths_df.to_sql("concepts",engine,index_label='id',if_exists="replace")
    stock_a_spot_em_df.to_sql("securities",engine,index_label='id',if_exists="replace")   

