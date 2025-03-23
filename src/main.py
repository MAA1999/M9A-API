from getContent import *
from analyzeContent import *

for resource in ["cn", "en", "jp"]:
    success, result = getContent(resource)
    if success:
        soup = analyzeContent(resource, result[-1])