import numpy
from silx.gui import qt
from silx.gui.plot import Plot2D

DEBUG = 0

class PyMcaImageWindow(qt.QWidget):
    def __init__(self, parent=None, backend="gl"):
        super(PyMcaImageWindow, self).__init__(parent)
        self.mainLayout = qt.QVBoxLayout(self)
        self.plot = Plot2D(self, backend=backend)
        self.mainLayout.addWidget(self.plot)

    def _removeSelection(self, *var):
        print("_removeSelection to be implemented")

    def _replaceSelection(self, *var):
        print("_removeSelection to be implemented")

    def _addSelection(self, selectionlist):
        if DEBUG:
            print("_addSelection(self, selectionlist)",selectionlist)
        if type(selectionlist) == type([]):
            sellist = selectionlist
        else:
            sellist = [selectionlist]

        for sel in sellist:
            source = sel['SourceName']
            key    = sel['Key']
            legend = sel['legend'] #expected form sourcename + scan key
            dataObject = sel['dataobject']
            #only two-dimensional selections considered
            if dataObject.info.get("selectiontype", "1D") != "2D":
                continue
            if not hasattr(dataObject, "x"):
                raise TypeError("Not a scatter plot. No axes")
            elif len(dataObject.x) != 2:
                raise TypeError("Not a scatter plot. Invalid number of axes.")
            for i in range(len(dataObject.x)):
                if numpy.isscalar(dataObject.x[i]):
                    dataObject.x[i] = numpy.array([dataObject.x[i]])
            if hasattr(dataObject, "data") and not hasattr(dataObject, "y"):
                dataObject.y = [data]
            if not hasattr(dataObject, "y"):
                raise TypeError("Not a scatter plot. No signal.")
            elif dataObject.y is None:
                raise TypeError("Not a scatter plot. No signal.")
            elif not len(dataObject.y):
                raise TypeError("Not a scatter plot. No signal.")
            for i in range(len(dataObject.y)):
                if numpy.isscalar(dataObject.y[i]):
                    dataObject.y[i] = numpy.array([dataObject.y[i]])
            # we only deal with one signal, if there are more, they should be separated
            # in different selections
            x = numpy.ascontiguousarray(dataObject.x[0])[:]
            y = numpy.ascontiguousarray(dataObject.x[1])[:]
            data = numpy.ascontiguousarray(dataObject.y[0])[:]
            if (data.size == x.size) and (data.size == y.size):
                # standard scatter plot
                data.shape = 1, -1
                nscatter = 1
            elif (x.size == y.size) and ((data % x.size) == 0):
                # we have n items, assuming they follow C order we can collapse them to
                # something that can be viewed. In this case (scatter) we can sum. The
                # only problem is that if we have a multidimensional monitor we have to
                # normalize first.
                oldDataShape = data.shape
                n = 1
                gotIt = False
                for i in range(len(oldDataShape)):
                    n *= oldDataShape[i]
                    if n == x.size:
                        gotIt = True
                        break
                if not gotIt:
                    raise ValueError("Unmatched dimensions following C order")
                data.shape = xsize, oldDataShape[i+1:]
                nscatter = data.shape[0]
            else:
                raise ValueError("Unmatched dimensions among axes and signals")

            # deal with the monitor
            if hasattr(dataObject, 'm'):
                if dataObject.m is not None:
                    for m in dataObject.m:
                        if numpy.isscalar(m):
                            data /= m
                        elif m.size == 1:
                            data /= m[0]
                        elif (m.size == data.shape[0]) and (m.size == data[0].shape):
                            # resolve an ambiguity, for instance, monitor has 10 values
                            # and the data to be normalized are 10 x 10
                            if len(m.shape) > 1:
                                # the monitor was multidimensional.
                                # that implies normalization "per pixel"
                                for i in range(data[0].shape):
                                    data[i] /= m.reshape(data[i].shape)
                            else:
                                # the monitor was unidimensional.
                                # that implies normalization "per acquisition point"
                                for i in range(m.size):
                                    data[i] /= m[i]                                
                        elif m.size == data.shape[0]:
                            for i in range(m.size):
                                data[i] /= m[i]
                        elif m.size == data[0].shape:
                            for i in range(data[0].shape):
                                data[i] /= m.reshape(data[i].shape)
                        elif m.size == data.size:
                            # potentially can take a lot of memory, numexpr?
                            data /= m.reshape(data.shape)
                        else:
                            raise ValueError("Incompatible monitor data")                            
            while len(data.shape) > 2:
                # collapse any additional dimension by summing
                data = data.sum(dtype=numpy.float32, axis=-1).astype(numpy.float32)
            dataObject.data = data
            x.shape = -1
            y.shape = -1
            dataObject.x = [x, y]
            self.dataObjectsList = [legend]
            self.dataObjectsDict = {legend:dataObject}
        self.showData(0)
        self.plot.resetZoom()

    def showData(self, index=0, moveslider=True):
        legend = self.dataObjectsList[0]
        dataObject = self.dataObjectsDict[legend]
        shape = dataObject.data.shape
        x = dataObject.x[0]
        y = dataObject.x[1]
        #x.shape = -1
        #y.shape = -1
        values = dataObject.data[index]
        #values.shape = -1
        self.plot.remove(kind="scatter")
        self.plot.addScatter(x, y, values, legend=legend, info=dataObject.info)
        txt = "%s %d" % (legend, index)
        #self.setName(txt)
        #if moveslider:
        #    self.slider.setValue(index)

    def setPlotEnabled(self, value=True):
        self._plotEnabled = value
        if value:
            self.showData()

class TimerLoop:
    def __init__(self, function = None, period = 1000):
        self.__timer = qt.QTimer()
        if function is None: function = self.test
        self._function = function
        self.__setThread(function, period)
        #self._function = function

    def __setThread(self, function, period):
        self.__timer = qt.QTimer()
        self.__timer.timeout[()].connect(function)
        self.__timer.start(period)

    def test(self):
        print("Test function called")

if __name__ == "__main__":
    from PyMca5 import DataObject
    import weakref
    import time
    import sys
    def buildDataObject(arrayData):
        dataObject = DataObject.DataObject()
        #dataObject.data = arrayData
        dataObject.y = [arrayData]
        x1, x0 = numpy.meshgrid(10 * numpy.arange(arrayData.shape[0]), numpy.arange(arrayData.shape[1]))
        dataObject.x = [x1, x0]
        dataObject.info['selectiontype'] = "2D"
        dataObject.info['Key'] = id(dataObject)
        return dataObject

    def buildSelection(dataObject, name = "image_data0"):
        key = dataObject.info['Key']
        def dataObjectDestroyed(ref, dataObjectKey=key):
            if DEBUG:
                print("dataObject distroyed key = %s" % key)
        dataObjectRef=weakref.proxy(dataObject, dataObjectDestroyed)
        selection = {}
        selection['SourceType'] = 'SPS'
        selection['SourceName'] = 'spec'
        selection['Key']        = name
        selection['legend']     = selection['SourceName'] + "  "+ name
        selection['imageselection'] = False
        selection['dataobject'] = dataObjectRef
        return selection

    a = 1000
    b = 1000
    period = 1000
    x1 = numpy.arange(a * b).astype(numpy.float)
    x1.shape= [a, b]
    x2 = numpy.transpose(x1)
    print("INPUT SHAPES = ", x1.shape, x2.shape)

    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)
    if len(sys.argv) > 1:PYMCA=True
    else:PYMCA = False

    if PYMCA:
        from PyMca5.PyMcaGui import PyMcaMain
        w = PyMcaMain.PyMcaMain()
        w.show()
    else:
        w = PyMcaImageWindow()
        w.show()
    counter = 0
    def function(period = period):
        global counter
        flag = counter % 6
        if flag == 0:
            #add x1
            print("Adding X1", x1.shape, x2.shape)
            dataObject = buildDataObject(x1)
            selection = buildSelection(dataObject, 'X1')
            if PYMCA:
                w.dispatcherAddSelectionSlot(selection)
            else:
                w._addSelection(selection)
        elif flag == 1:
            #add x2
            print("Adding X2", x1.shape, x2.shape)
            dataObject = buildDataObject(x2)
            selection = buildSelection(dataObject, 'X2')
            if PYMCA:
                w.dispatcherAddSelectionSlot(selection)
            else:
                w._addSelection(selection)
        elif flag == 2:
            #add x1
            print("Changing X1", x1.shape, x2.shape)
            dataObject = buildDataObject(x2)
            selection = buildSelection(dataObject, 'X1')
            if PYMCA:
                w.dispatcherAddSelectionSlot(selection)
            else:
                w._addSelection(selection)
        elif flag == 1:
            #add x2
            print("Changing X2", x1.shape, x2.shape)
            dataObject = buildDataObject(x2)
            selection = buildSelection(dataObject, 'X1')
            if PYMCA:
                w.dispatcherAddSelectionSlot(selection)
            else:
                w._addSelection(selection)
        elif flag == 4:
            #replace x1
            print("Replacing by new X1", x1.shape, x2.shape)
            dataObject = buildDataObject(x1-x2)
            selection = buildSelection(dataObject, 'X1')
            if PYMCA:
                w.dispatcherReplaceSelectionSlot(selection)
            else:
                w._replaceSelection(selection)
        else:
            #replace by x2
            print("Replacing by new X2", x1.shape, x2.shape)
            dataObject = buildDataObject(x2-x1)
            selection = buildSelection(dataObject, 'X2')
            if PYMCA:
                w.dispatcherReplaceSelectionSlot(selection)
            else:
                w._replaceSelection(selection)
        counter += 1

    loop = TimerLoop(function = function, period = period)
    sys.exit(app.exec_())
