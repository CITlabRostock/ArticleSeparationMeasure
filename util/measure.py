from __future__ import print_function
import numpy as np
from collections import namedtuple


BaselineMeasureResult = namedtuple("BaselineMeasureResult", ["pageWisePerDistTolTickPerLineRecall",
                                                             "pageWisePerDistTolTickRecall",
                                                             "pageWiseRecall",
                                                             "recall",
                                                             "pageWisePerDistTolTickPerLinePrecision",
                                                             "pageWisePerDistTolTickPrecision",
                                                             "pageWisePrecision",
                                                             "precision"])


class BaselineMeasure(object):
    def __init__(self):
        self.result = BaselineMeasureResult(pageWisePerDistTolTickPerLineRecall=[],
                                            pageWisePerDistTolTickRecall=[],
                                            pageWiseRecall=[],
                                            recall=0.0,
                                            pageWisePerDistTolTickPerLinePrecision=[],
                                            pageWisePerDistTolTickPrecision=[],
                                            pageWisePrecision=[],
                                            precision=0.0)

    def addPerDistTolTickPerLineRecall(self, perDistTolTickPerLineRecall):
        """ #distTolTicks x #truthBaseLines matrix of recalls"""
        assert len(perDistTolTickPerLineRecall.shape) == 2
        self.result.pageWisePerDistTolTickPerLineRecall.append(perDistTolTickPerLineRecall)
        aPageWisePerDistTolTickRecall = np.zeros(perDistTolTickPerLineRecall.shape[0])
        for i in range():
            pass





t = np.zeros([5,4,3])
print(t.shape)
print(len(t.shape))
