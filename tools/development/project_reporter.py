class ProjectReporter:
    """
    Generates project intelligence reports.
    """


    def generate(self, analysis):

        return f"""
Ahmed AI Project Intelligence Report

Files:
{analysis['file_count']}

Languages:
{analysis['languages']}

Directories:
{analysis['directory_count']}

Observations:
{analysis['observations']}
"""
