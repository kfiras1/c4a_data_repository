# -*- coding: utf-8 -*-

"""

The main controller class of the REST API. This class contains the common actions to manage general request
from the API.

"""


from __future__ import print_function

import os
import inspect
import ConfigParser
import logging
from sqlalchemy import create_engine, desc
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"

# Database settings
config = ConfigParser.ConfigParser()
# Checks actual path of the file and sets config file.
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
config_dir = os.path.abspath(current_dir + '../../../conf/rest_api.cfg')
config.read(config_dir)

if 'database' in config.sections():
    # We have config file with data
    DATABASE = {
        'drivername': config.get('database', 'drivername') or 'postgres',
        'host': config.get('database', 'host') or 'localhost',
        'port': config.get('database', 'port') or '5432',
        'username': config.get('database', 'username') or 'postgres',
        'password': config.get('database', 'password') or 'postgres',
        'database': config.get('database', 'database') or 'postgres'
    }
else:
    # Any config file detected, load default settings.
    DATABASE = {
        'drivername': 'postgres',
        'host': 'localhost',
        'port': '5432',
        'username': 'postgres',
        'password': 'postgres',
        'database': 'postgres'
    }


class PostORM(object):

    def __init__(self, autoflush=True):
        # Make basic connection and setup declarative
        self.engine = create_engine(URL(**DATABASE))
        try:
            session_mark = sessionmaker(bind=self.engine)  # Bind session engine Test connection
            session = session_mark()
            if session:
                print("Connection OK")
                if autoflush:
                    logging.info("Created session connection with autoflush")
                    self.session = session
                else:
                    logging.info("Created session connection without autoflush")
                    self.session = session.no_autoflush
        except OperationalError:
            print ("Database arguments are invalid")

    def flush(self):
        """
        Force flush the actual session. Usefull for non autoflush created sessions

        :return: None
        """
        self.session.flush()

    def refresh(self, p_data):
        """
        Force refresh to pending data to obtain i'ts direct ID
        
        :param p_data: 
        :return: The updated data
        """
        self.session.refresh(p_data)

    def insert_one(self, p_data):
        """
        Insert one desired data

        :param p_data: Object from Tables
        :return: None
        """
        self.session.add(p_data)

    def insert_all(self, p_list_data):
        """
        Insert a list of Type of datas

        :param p_list_data: List of data
        :return: None
        """
        self.session.add_all(p_list_data)  # Multiple users, pending action

    def count(self, p_table):
        """
        Counts the total row of a defined table in database

        :return: The number of elements of a table
        """
        #number_elements = self.session.

    def query(self, p_class, web_dict, limit=10, offset=0, order_by='asc'):
        """
        Makes a query to the desired table of database and filter the result based on user choice.

        :param p_class:  Name of the table to query
        :param web_dict: A dict with columns and data to filter.
        :param limit: query limit (default is 10)
        :param offset: offset (default is 0)
        :param order_by: Set order of query (default is 'asc' on ID column)
        :return:
        """
        q = self.session.query(p_class)
        if q and web_dict and web_dict.items():
            # Filter based of the content of the dict
            for attr, value in web_dict.items():
                q = q.filter(getattr(p_class, attr).like("%%%s%%" % value))
        # ORder by
        if order_by is not 'asc':
            # Default order by id
            q = q.order_by(desc(p_class.id))
        # Limit and offset our query
        q = q.limit(limit)
        q = q.offset(offset)
        return q

    def query_get(self, p_class, p_id):
        """
        Makes a query to the desired Table of databased based on row ID

        :param p_class:  Name of the table to query
        :param p_id: id of the row
        :return: Object instance of the class or None
        """
        q = None
        res = self.session.query(p_class).get(p_id)
        if res:
            q = res
        return q

    def commit(self):
        """
        Commit all data and close the connection to DB.

        :return: True if commit is successfully done.
                 False if there are any error in db
        """
        res = False
        try:
            self.session.commit()
            # Commit successful
            logging.info("post_orm: commit successful")
            res = True
        except Exception as e:
            logging.exception("post_orm: An error happened when commit in DB: %s", e)
            self.session.rollback()
        return res

    def close(self):
        """
        Force close the connecion of the actual session

        :return: None
        """
        if self.session:
            self.session.close()

    def _get_or_create(self, model, **kwargs):
        # type: (object, object) -> object
        """
        This method creates a new entry in db if this isn't exist yet or retrieve the instance information based on
        some arguments.

        :param model: The Table name defined in Tables class
        :param kwargs: The needed arguments to create the table for example

                (id=23, name='pako', lastname='rodriguez')

        :return: An instance of  the Table.
        """
        instance = self.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            self.insert_one(instance)
            self.commit()
            return instance
