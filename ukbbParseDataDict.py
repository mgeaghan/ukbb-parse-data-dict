from bs4 import BeautifulSoup
import pandas as pd


class ukbbHtmlParser():
    def _formatTable(self, table):
        tmp = table.find_all("tr")
        tmpHead = tmp[0]
        tmpRows = tmp[1:]
        header = [h.get_text() for h in tmpHead.find_all("th")]
        rows = [
            [data.get_text("\n") for data in row.find_all("td")]
            for row in tmpRows
        ]
        rowspan = []
        for i_tr, tr in enumerate(tmpRows):
            tmp = []
            for i_td, td in enumerate(tr.find_all("td")):
                if "rowspan" in td.attrs:
                    rowspan.append(
                        (i_tr, i_td, int(td["rowspan"]), td.get_text("\n"))
                    )
        if len(rowspan) > 0:
            for i in rowspan:
                for j in range(1, i[2]):
                    rows[i[0] + j].insert(i[1], i[3])
        tableDict = {h: [] for h in header}
        for i, h in enumerate(header):
            for r in rows:
                tableDict[h].append(r[i])
        return tableDict

    def _formatHeading(self, heading):
        return heading.get_text()

    def _compileTables(self, tableHeadingFormattedList, tableHeadingTagList):
        dataList = []
        for i, tag in enumerate(tableHeadingTagList):
            if tag in ["h1", "h3"]:
                dataList.append({
                    "heading": tableHeadingFormattedList[i],
                    "tables": []
                })
            else:
                dataList[-1]["tables"].append(tableHeadingFormattedList[i])
        return dataList

    def _tablesToPandas(self, dataList):
        newDataList = []
        for d in dataList:
            heading = d["heading"]
            newTables = [pd.DataFrame.from_dict(t) for t in d["tables"]]
            newDataList.append({"heading": heading, "tables": newTables})
        return newDataList

    def __init__(self, file):
        with open(file, "r", errors="replace") as f:
            self.html = BeautifulSoup("".join(f.readlines()),
                                      "html5lib")
        self.headingsAndTables = self.html.find_all(["h1", "h3", "table"])
        self.headingsAndTablesTags = [i.name for i in self.headingsAndTables]
        self.headingsAndTablesFormatted = [
            self._formatHeading(x) if (
                self.headingsAndTablesTags[i] in ["h1", "h3"]
            )
            else self._formatTable(x)
            for i, x in enumerate(self.headingsAndTables)
        ]
        self.data = self._tablesToPandas(
            self._compileTables(
                self.headingsAndTablesFormatted,
                self.headingsAndTablesTags
            )
        )

    def search(self, text, dataframe=True):
        textTrack = {
            "data": [],
            "dataIdx": [],
            "tableIdx": [],
            "column": [],
            "rowIdx": []
        }
        for di, d in enumerate(self.data):
            tables = d["tables"]
            for ti, t in enumerate(tables):
                for col in t:
                    textPos = [
                        i for i, v in enumerate(t[col])
                        if text.lower() in v.lower()
                    ]
                    for i in textPos:
                        textTrack["data"].append(d["heading"])
                        textTrack["dataIdx"].append(di)
                        textTrack["tableIdx"].append(ti)
                        textTrack["column"].append(col)
                        textTrack["rowIdx"].append(i)
        if dataframe:
            return pd.DataFrame(textTrack)
        else:
            return textTrack

    def searchByDataCoding(self, num, dataframe=True):
        return self.search(
            "data-coding \n" + str(num) + "\n",
            dataframe=dataframe
        )

    def getRows(self, searchResults):
        dataIdx = searchResults.dataIdx
        tableIdx = searchResults.tableIdx
        tables = {}
        uniqe_tables = list(set([t for t in zip([*dataIdx], [*tableIdx])]))
        for d, t in uniqe_tables:
            sub_searchResults = searchResults[
                (searchResults.dataIdx == d) &
                (searchResults.tableIdx == t)
            ]
            rows = sub_searchResults.rowIdx
            name = (
                [*sub_searchResults.data][0] +
                " | " +
                str([*sub_searchResults.tableIdx][0])
            )
            tables[name] = self.data[d]['tables'][t].iloc[rows]
        return tables

    def prettyPrintRows(self, rows):
        for k in rows.keys():
            print(str(k) + ":\n")
            print(rows[k])
            print("\n==========\n")

    def getTableByHeading(self, heading):
        return [d for d in self.data if d["heading"] == heading]

    def getDataCoding(self, num):
        return self.getTableByHeading("Data-Coding " + str(num))

    def prettyPrintDataCoding(self, dataCodingResults):
        for d in dataCodingResults:
            dataCoding = str(d['heading'])
            print(dataCoding + ":\n")
            for i, t in enumerate(d['tables']):
                table = dataCoding + " | " + str(i)
                print(table + ":\n")
                print(t)
                print("\n")
            print("\n==========\n")
