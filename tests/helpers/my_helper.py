from datetime import datetime
import unittest
import logging

class MyHelper():

    @classmethod
    def days_ago(cls, d):
        return (datetime.now().date() - d).days