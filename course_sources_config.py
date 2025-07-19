"""
Course Sources Configuration
===========================

This module defines and manages allowed course sources for the AI Learning Tracker.
Only includes Microsoft-owned platforms and open-source/free educational platforms.

Avoids paid-only or unverified sources to ensure quality and accessibility.
"""

from enum import Enum
from typing import Dict, List, Set

class CourseSourceType(Enum):
    """Types of course sources"""
    MICROSOFT = "microsoft"
    OPEN_SOURCE = "open_source" 
    FREE_EDUCATION = "free_education"
    ACADEMIC = "academic"

class AllowedCourseSources:
    """Configuration for allowed course sources"""
    
    # Microsoft-owned platforms
    MICROSOFT_SOURCES = {
        'Microsoft Learn': {
            'type': CourseSourceType.MICROSOFT,
            'priority': 1,
            'verified': True,
            'description': 'Official Microsoft learning platform'
        },
        'LinkedIn Learning': {
            'type': CourseSourceType.MICROSOFT,
            'priority': 2,
            'verified': True,
            'description': 'Professional development courses (Microsoft-owned)'
        }
    }
    
    # Open-source and free educational platforms
    FREE_EDUCATION_SOURCES = {
        'Coursera': {
            'type': CourseSourceType.FREE_EDUCATION,
            'priority': 3,
            'verified': True,
            'description': 'University courses and specializations (free content available)'
        },
        'edX': {
            'type': CourseSourceType.FREE_EDUCATION,
            'priority': 3,
            'verified': True,
            'description': 'University-backed online courses (free auditing available)'
        },
        'Khan Academy': {
            'type': CourseSourceType.FREE_EDUCATION,
            'priority': 4,
            'verified': True,
            'description': 'Free educational content for all ages'
        },
        'FreeCodeCamp': {
            'type': CourseSourceType.OPEN_SOURCE,
            'priority': 4,
            'verified': True,
            'description': 'Free coding bootcamp and tutorials'
        },
        'MIT OpenCourseWare': {
            'type': CourseSourceType.ACADEMIC,
            'priority': 3,
            'verified': True,
            'description': 'Free MIT university course materials'
        },
        'Stanford Online': {
            'type': CourseSourceType.ACADEMIC,
            'priority': 3,
            'verified': True,
            'description': 'Stanford University online courses'
        }
    }
    
    # Open-source technology platforms
    OPEN_SOURCE_SOURCES = {
        'Google AI Education': {
            'type': CourseSourceType.OPEN_SOURCE,
            'priority': 2,
            'verified': True,
            'description': 'Google AI and machine learning resources'
        },
        'PyTorch Foundation': {
            'type': CourseSourceType.OPEN_SOURCE,
            'priority': 3,
            'verified': True,
            'description': 'Official PyTorch tutorials and courses'
        },
        'TensorFlow': {
            'type': CourseSourceType.OPEN_SOURCE,
            'priority': 3,
            'verified': True,
            'description': 'Official TensorFlow learning resources'
        },
        'Hugging Face': {
            'type': CourseSourceType.OPEN_SOURCE,
            'priority': 3,
            'verified': True,
            'description': 'Open-source NLP and AI model hub'
        },
        'Kaggle Learn': {
            'type': CourseSourceType.OPEN_SOURCE,
            'priority': 4,
            'verified': True,
            'description': 'Free micro-courses for data science and AI'
        },
        'AWS Training': {
            'type': CourseSourceType.FREE_EDUCATION,
            'priority': 4,
            'verified': True,
            'description': 'AWS digital training (free content available)'
        },
        'Google Cloud': {
            'type': CourseSourceType.FREE_EDUCATION,
            'priority': 4,
            'verified': True,
            'description': 'Google Cloud training and certification (free content available)'
        }
    }
    
    # Specialized AI/Educational sources
    EDUCATIONAL_SOURCES = {
        'Educational Resources': {
            'type': CourseSourceType.FREE_EDUCATION,
            'priority': 5,
            'verified': True,
            'description': 'General educational content aggregation'
        },
        'Data Science Institute': {
            'type': CourseSourceType.ACADEMIC,
            'priority': 4,
            'verified': True,
            'description': 'Academic data science curriculum'
        },
        'AI Research Institute': {
            'type': CourseSourceType.ACADEMIC,
            'priority': 3,
            'verified': True,
            'description': 'Cutting-edge AI research and education'
        }
    }
    
    @classmethod
    def get_all_allowed_sources(cls) -> Dict[str, Dict]:
        """Get all allowed course sources"""
        all_sources = {}
        all_sources.update(cls.MICROSOFT_SOURCES)
        all_sources.update(cls.FREE_EDUCATION_SOURCES)
        all_sources.update(cls.OPEN_SOURCE_SOURCES)
        all_sources.update(cls.EDUCATIONAL_SOURCES)
        return all_sources
    
    @classmethod
    def get_source_names(cls) -> Set[str]:
        """Get set of all allowed source names"""
        return set(cls.get_all_allowed_sources().keys())
    
    @classmethod
    def is_allowed_source(cls, source_name: str) -> bool:
        """Check if a source is allowed"""
        return source_name in cls.get_source_names()
    
    @classmethod
    def get_sources_by_type(cls, source_type: CourseSourceType) -> Dict[str, Dict]:
        """Get sources filtered by type"""
        all_sources = cls.get_all_allowed_sources()
        return {
            name: details for name, details in all_sources.items()
            if details['type'] == source_type
        }
    
    @classmethod
    def get_high_priority_sources(cls) -> Dict[str, Dict]:
        """Get high priority sources (priority 1-3)"""
        all_sources = cls.get_all_allowed_sources()
        return {
            name: details for name, details in all_sources.items()
            if details['priority'] <= 3
        }

# Export main functionality
ALLOWED_SOURCES = AllowedCourseSources.get_all_allowed_sources()
SOURCE_NAMES = AllowedCourseSources.get_source_names()

def validate_course_source(source_name: str) -> bool:
    """Validate if a course source is allowed"""
    return AllowedCourseSources.is_allowed_source(source_name)

def get_source_description(source_name: str) -> str:
    """Get description for a source"""
    sources = AllowedCourseSources.get_all_allowed_sources()
    return sources.get(source_name, {}).get('description', 'Unknown source')

def get_microsoft_sources() -> List[str]:
    """Get list of Microsoft-owned platform names"""
    microsoft_sources = AllowedCourseSources.get_sources_by_type(CourseSourceType.MICROSOFT)
    return list(microsoft_sources.keys())

def get_free_education_sources() -> List[str]:
    """Get list of free education platform names"""
    free_sources = AllowedCourseSources.get_sources_by_type(CourseSourceType.FREE_EDUCATION)
    return list(free_sources.keys())

def get_open_source_sources() -> List[str]:
    """Get list of open-source platform names"""
    open_sources = AllowedCourseSources.get_sources_by_type(CourseSourceType.OPEN_SOURCE)
    return list(open_sources.keys())
