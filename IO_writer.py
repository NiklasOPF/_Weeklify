import pandas as pd
from os.path import exists

import xlsxwriter as xlsxwriter

_configuration_sheet_name = 'Configuration' # used to identify the excel sheet of a configuration.
_records_sheet_name = 'Records' # used to identify the excel sheet of a configuration.
perormance_report_sheet_name = 'PerformanceReport' # Used to summarize the

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class IO:
    def __init__(self):
        self.a = 1

    ################################### READ FUNCTIONS ###################################

    def ReadSheetWithSingleHeader(self, fileName, sheetName):
        inputDF = pd.read_excel(fileName, sheet_name=sheetName)
        inputDF['Date'] = pd.to_datetime(inputDF['Date'])
        return inputDF.set_index('Date').dropna(how='all')

    def ReadUtilityFunctions(self, fileName):
        df = self.ReadSheetWithSingleHeader(fileName, sheetName=_configuration_sheet_name)
        if df.isnull().values.any():
            raise ValueError("Configuration tab of the input dataframe contains empty cells")
        return df

    def ReadPerformanceRecords(self, fileName):
        df = self.ReadSheetWithSingleHeader(fileName, sheetName=_records_sheet_name)
        self.CheckThatNoUnallowedStringsExistInTheInput(df)
        return df

    ################################### WRITE FUNCTIONS ###################################

    def WriteDataFrameToExcel(self, df, fileName, sheetname):
        # If file does not exist, generate a new file and append all the base sheets
        if not exists(fileName):
            workbook = xlsxwriter.Workbook(fileName)
            worksheet2 = workbook.add_worksheet(sheetname)
            workbook.close()

        # Write the selected sheet as output
        with pd.ExcelWriter(fileName, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheetname)

    def SavePerformanceReport(self, perfromanceReportRecord, inputFileName, outputFileName):
        # Read existing performance report
        performanceReport = self.ReadSheetWithSingleHeader(inputFileName, perormance_report_sheet_name)

        # Merge existing performance report with new record
        df = perfromanceReportRecord.combine_first(performanceReport).sort_index()
        df = df.reindex(sorted(df.columns), axis=1)
        column_to_move = df.pop("Total")
        df.insert(len(df.columns), "Total", column_to_move)
        df.index.name = 'Date'

        self.WriteDataFrameToExcel(df, outputFileName, perormance_report_sheet_name)

    ################################### DQ AND HELPER METHODS ###################################

    def CheckThatNoUnallowedStringsExistInTheInput(self, df):
        if df.isnull().values.any():
            raise ValueError("Records tab of the input dataframe contains empty cells")
        for rowIndex, row in df.iterrows():  # iterate over rows
            for columnIndex, value in row.items():
                if isinstance(value, str):
                    if value != "-"and not is_number(value):
                        raise ValueError("input filed at index [" + str(rowIndex) + ", " + str(
                            columnIndex) + "] has the value: " + str(value) + ". This is not an allowed input.")

    def CheckCompatibilityBetweenReadDFs(self, records, configuration):
        # 1. ENSURE DIMENSIONS OF DFs are the same
        if records.shape != configuration.shape:
            raise RuntimeError("The shape of the records sheet is: " + str(records.shape) + ", whereas the shape of the configuration sheet is: " + str(configuration.shape) + ". Please ensure that the number of populated columns and rows match.")
        # 2. ENSURE THAT THE COLUMN NAMES ARE THE SAME
        if not configuration.columns.equals(records.columns):
            outerJoin = set(configuration.columns) ^ set(records.columns)
            raise RuntimeError("The column names in the records sheet does not match the column names in the configuration sheet. Specifically, there is a non-overlap betwen: " + str(outerJoin) + ". Please ensure that the columns are equal")

    ################################### OUTDATED METHODS ###################################

    def ReadSheetWithMultiHeader(self, fileName, sheetName):
        inputDF = pd.read_excel(fileName, sheet_name=sheetName, header=None)
        header = []
        for i in range(inputDF.shape[1]): # skip fist index since it's only the date
            if inputDF.iloc[0, i] == 'Total':
                header.append('Total')
            else:
                header.append(inputDF.iloc[0, i] + " - " + inputDF.iloc[1, i])
        body = inputDF.iloc[2:]
        body.iloc[:,0] = pd.to_datetime(body.iloc[:,0])
        df = pd.concat([pd.DataFrame(header).T.set_index(0), body.set_index(0).dropna(how='all')])
        df.columns = df.iloc[0]
        return df[1:]

