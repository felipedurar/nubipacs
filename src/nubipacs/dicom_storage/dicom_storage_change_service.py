from datetime import datetime

from nubipacs.utils.singleton_meta import SingletonMeta

STUDY_CHANGE_LIST = []

class DicomStorageChangeService(metaclass=SingletonMeta):

    def report_study_changed(self, study_instance_uid):
        study_report = self.find_study_changed(study_instance_uid)
        if study_report is None:
            study_report = {
                "study_instance_uid": study_instance_uid
            }
            STUDY_CHANGE_LIST.append(study_report)
        study_report['change_datetime'] = datetime.now()

    def find_study_changed(self, study_instance_uid):
        for c_study in STUDY_CHANGE_LIST:
            if c_study['study_instance_uid'] == study_instance_uid:
                return c_study
        return None

    def get_change_list(self):
        global STUDY_CHANGE_LIST
        return STUDY_CHANGE_LIST

    def clear_change_list(self):
        global STUDY_CHANGE_LIST
        STUDY_CHANGE_LIST = []