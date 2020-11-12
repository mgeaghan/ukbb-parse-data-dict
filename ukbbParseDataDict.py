import html.parser as hp


class ukbbData():
    def __checkInstance(self, objType):
        def isInst(x):
            return isinstance(x, objType)
        return isInst

    def checkHeading(self, headingStr):
        if (self.__checkInstance(str)(headingStr)):
            return headingStr
        else:
            return ""

    def checkDescription(self, descriptionStr):
        if (self.__checkInstance(str)(descriptionStr)):
            return descriptionStr
        else:
            return ""

    def checkData(self, dataList):
        if (self.__checkInstance(list)(dataList) and False not in list(map(self.__checkInstance(dict), dataList))):
            return dataList
        else:
            return []

    def __init__(self, heading="", description="", data=[]):
        self.heading = self.checkHeading(heading)
        self.description = self.checkDescription(description)
        self.data = self.checkData(data)
        # self.__isStr = self.__checkInstance(str)
        # self.__isList = self.__checkInstance(list)
        # self.__isDict = self.__checkInstance(dict)

    def setHeading(self, headingStr):
        self.heading = self.checkHeading(headingStr)

    def setDescription(self, descriptionStr):
        self.description = self.checkDescription(descriptionStr)

    def setData(self, dataList):
        self.data = self.checkData(dataList)

    def addData(self, dataDict):
        if (self.__checkInstance(dict)(dataDict)):
            self.data.append(dataDict)

    def makeDict(self):
        return {"heading": self.heading,
                "description": self.description,
                "data": self.data}


class ukbbHtmlParser(hp.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ukbbData = []
        self.ukbbSection = None
        self.heading = ""
        self.text = ""
        self.firstSection = True
        self.newHeading = False
        self.newTable = False
        self.newRow = False
        self.newHeader = False
        self.newData = False
        self.rowCount = 0
        self.colCount = 0
        self.tableDict = {}
        self.tableHeaders = []
        self.rowspan = 1

    def updateUkbbData(self):
        if isinstance(self.ukbbSection, ukbbData):
            self.ukbbData.append(self.ukbbSection.makeDict())

    def handle_starttag(self, tag, attrs):
        if tag in ["h1", "h3"]:
            if not self.firstSection:  # when starting a new section, push the previous section to the list of tables, unless this is the very first section
                self.updateUkbbData()
            else:
                self.firstSection = False
            self.ukbbSection = None  # erase the previous section, along with its heading and text
            self.heading = ""
            self.text = ""
            self.newHeading = True
        elif tag == "table":
            self.newTable = True
            self.tableDict = {}  # erase the previous table, along with its headers
            self.rowCount = 0
            self.tableHeaders = []  # keep track of the header labels
        elif self.newTable:
            if tag == "tr":
                self.newRow = True
                self.colCount = 0
            elif self.newRow:
                if tag == "th":
                    self.newHeader = True
                elif self.tableHeaders != [] and tag == "td":
                    self.newData = True
                    if "rowspan" in [i[0] for i in attrs]:  # if a column's value spans over multiple rows, take not of how many
                        self.rowspan = int(attrs[[i[0] for i in attrs].index("rowspan")][1])
                    else:
                        self.rowspan = 1
                        h = self.tableHeaders[self.colCount]
                        while len(self.tableDict[h]) >= self.rowCount:  # account for previous rowspans that have already been filled; if xth column for yth row already filled, move to (x+1)th column; rowCount 0 = header, rowCount 1 = 1st row, etc
                            self.colCount += 1
                            h = self.tableHeaders[self.colCount]

    def handle_data(self, data):
        if self.newHeading:
            self.heading = data  # set the section heading
        elif self.newRow:
            if self.newHeader:
                self.tableDict[data] = []  # create a new column
                self.tableHeaders.append(data)  # set the new header name
            elif self.tableHeaders != [] and self.newData:
                h = self.tableHeaders[self.colCount]  # get header name for current column
                if len(self.tableDict[h]) == self.rowCount - 1:  # if xth column for yth row hasn't been filled, fill it
                    self.tableDict[h].append(data)
                elif len(self.tableDict[h]) == self.rowCount:  # if xth column for yth row has already been filled - this should only occur if there are additional tags in the cell, e.g. <a>'s - append the new data to the existing data
                    self.tableDict[h][-1] += "\n" + data

        else:  # accumulate any non-tabulated text in a string
            if self.text == "":
                self.text = data
            else:
                self.text += "\n" + data

    def handle_endtag(self, tag):
        if tag in ["h1", "h3"]:
            self.newHeading = False
        elif tag == "tr":
            self.newRow = False
            self.rowCount += 1
        elif tag in ["th", "td"]:
            if self.rowspan > 1:  # if the current cell spans multiple rows
                h = self.tableHeaders[self.colCount]  # get header name for current column
                self.tableDict[h] += [self.tableDict[h][-1]] * (self.rowspan - 1)  # and replicate the cell the appropriate number of times
            self.colCount += 1
            self.newHeader = False
            self.newData = False
        elif tag == "table":  # once the end of a table is reached, add it to the current ukbbData object (or create one if it doesn't exist yet)
            if self.ukbbSection is None:
                self.ukbbSection = ukbbData(heading=self.heading, description=self.text, data=[self.tableDict])
            else:
                self.ukbbSection.addData(self.tableDict)
                self.ukbbSection.setDescription(self.text)  # update the non-tabulated text
            self.newTable = False
        elif tag == "html":
            self.ukbbSection.setDescription(self.text)  # update the non-tabulated text one last time
            self.updateUkbbData()  # push the final section to the list of tables
