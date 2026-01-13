import logging

INFO_SUMMARY = 21
INFO_DETAIL = 19

logging.addLevelName(INFO_SUMMARY, "INFO_SUMMARY")
logging.addLevelName(INFO_DETAIL, "INFO_DETAIL")


def info_summary(self, msg, *args, **kwargs):
    if self.isEnabledFor(INFO_SUMMARY):
        self._log(INFO_SUMMARY, msg, args, **kwargs)


def info_detail(self, msg, *args, **kwargs):
    if self.isEnabledFor(INFO_DETAIL):
        self._log(INFO_DETAIL, msg, args, **kwargs)


logging.Logger.info_summary = info_summary
logging.Logger.info_detail = info_detail
