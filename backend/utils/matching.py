from typing import Dict, List


SKILL_ALIASES: Dict[str, str] = {
    'reactjs':       'react',
    'react.js':      'react',
    'angularjs':     'angular',
    'vuejs':         'vue',
    'vue.js':        'vue',
    'nextjs':        'next.js',
    'nodejs':        'node.js',
    'node':          'node.js',
    'expressjs':     'express',
    'express.js':    'express',
    'springboot':    'spring boot',
    'golang':        'go',
    'ml':            'machine learning',
    'ai':            'artificial intelligence',
    'nlp':           'natural language processing',
    'cv':            'computer vision',
    'k8s':           'kubernetes',
    'sklearn':       'scikit-learn',
    'postgres':      'postgresql',
    'dotnet':        '.net',
    'tailwindcss':   'tailwind',
    'amazon web services': 'aws',
    'google cloud':  'gcp',
    'pyspark':       'spark',
    'huggingface':   'hugging face',
    'restful api':   'rest api',
    'restful apis':  'rest api',
    'rest apis':     'rest api',
    'object oriented programming': 'oop',
    'object-oriented programming': 'oop',
    'data analytics': 'data analysis',
    'powerbi':       'power bi',
    'ci cd':         'ci/cd',
}


def normalize_skill(skill: str) -> str:
    cleaned = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


