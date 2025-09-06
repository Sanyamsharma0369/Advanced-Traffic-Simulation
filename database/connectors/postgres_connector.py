"""
PostgreSQL Connector for Smart Traffic Light Controller System
Handles relational data storage and retrieval using SQLAlchemy
"""
import logging
from typing import Dict, List, Any, Optional, Type, Union
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.exc import SQLAlchemyError

from database.config.database_config import POSTGRES_CONFIG
from database.models.postgres_models import Base

logger = logging.getLogger(__name__)

class PostgresConnector:
    """Connector for PostgreSQL database operations"""
    
    def __init__(self):
        """Initialize PostgreSQL connection"""
        self.config = POSTGRES_CONFIG
        self.connection_string = (
            f"postgresql://{self.config['user']}:{self.config['password']}@"
            f"{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        
        self.engine = create_engine(
            self.connection_string,
            pool_size=self.config["min_connections"],
            max_overflow=self.config["max_connections"] - self.config["min_connections"],
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections after 30 minutes
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables defined in the models"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """
        Get a database session with automatic closing
        
        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def add_item(self, item: Base) -> bool:
        """
        Add a single item to the database
        
        Args:
            item: SQLAlchemy model instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.add(item)
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error adding item to database: {e}")
            return False
    
    def add_items(self, items: List[Base]) -> bool:
        """
        Add multiple items to the database
        
        Args:
            items: List of SQLAlchemy model instances
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.add_all(items)
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error adding items to database: {e}")
            return False
    
    def get_by_id(self, model_class: Type[Base], item_id: Union[str, int]) -> Optional[Base]:
        """
        Get an item by its ID
        
        Args:
            model_class: SQLAlchemy model class
            item_id: ID of the item
            
        Returns:
            Model instance if found, None otherwise
        """
        try:
            with self.get_session() as session:
                return session.query(model_class).filter(model_class.id == item_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting item by ID: {e}")
            return None
    
    def get_all(self, model_class: Type[Base], 
               filters: Optional[Dict[str, Any]] = None,
               limit: Optional[int] = None,
               offset: Optional[int] = None) -> List[Base]:
        """
        Get all items of a model class with optional filtering
        
        Args:
            model_class: SQLAlchemy model class
            filters: Optional dictionary of filter conditions
            limit: Optional limit on number of results
            offset: Optional offset for pagination
            
        Returns:
            List of model instances
        """
        try:
            with self.get_session() as session:
                query = session.query(model_class)
                
                if filters:
                    for key, value in filters.items():
                        if hasattr(model_class, key):
                            query = query.filter(getattr(model_class, key) == value)
                
                if limit is not None:
                    query = query.limit(limit)
                    
                if offset is not None:
                    query = query.offset(offset)
                    
                return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting items: {e}")
            return []
    
    def update_item(self, model_class: Type[Base], item_id: Union[str, int], 
                   update_data: Dict[str, Any]) -> bool:
        """
        Update an item by its ID
        
        Args:
            model_class: SQLAlchemy model class
            item_id: ID of the item
            update_data: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                item = session.query(model_class).filter(model_class.id == item_id).first()
                if not item:
                    return False
                    
                for key, value in update_data.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                        
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating item: {e}")
            return False
    
    def delete_item(self, model_class: Type[Base], item_id: Union[str, int]) -> bool:
        """
        Delete an item by its ID
        
        Args:
            model_class: SQLAlchemy model class
            item_id: ID of the item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                item = session.query(model_class).filter(model_class.id == item_id).first()
                if not item:
                    return False
                    
                session.delete(item)
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting item: {e}")
            return False
    
    def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query
        
        Args:
            query: SQL query string
            params: Optional parameters for the query
            
        Returns:
            List of result rows as dictionaries
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return [dict(row) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Error executing raw query: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()