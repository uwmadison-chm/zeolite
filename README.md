# zeolite

A python client for [MetricWire's Catalyst system](https://metricwire.com) API. API documentation is available on [Swaggerhub](https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/).

This library currently supports the following endpoints:

* [participants](https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/Participants/GetAllParticipants)
* [analysis](https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/Analysis/GetSubmissionsFromAnalysisPaginatedPII)
* [submissions](https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/Submissions/GetSubmissionsFromSurvey)
* [media](https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/Submissions/GetMediaSubmissionsFromSurveyPaginated)
* [sensor data](https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/Sensors/GetSensorSubmissionsFromStudyEnterprise)


### Installing

Zeolite is not currently in pypi. Currently, installation steps would be:

* Install the `requests` module.
* Put zeolite.py in your project.

This will hopefully change soon, with proper packaging.

### Usage

ID values for your project should be listed in a workspace's "Workspace API Reference" section.

```
import zeolite

# You'll need these values
workspace_id = ""
client_id = ""
client_secret = ""

ws = zeolite.Metricwire(workspace_id, client_id, client_secret)

# List participants
study_id = ""
for ppt in ws.participants_rows(study_id):
	print(ppt)


# Analysis results (probably what you want for survey responses)
analysis_id = ""
for row in ws.analysis_rows(analysis_id):
	print(row)


# Media (pictures / videos)
survey_id = ""
for row in ws.media_rows(study_id, survey_id):
	print(row)
	# Note that row["url"] will have a limited-time link to the media file


# Survey results (more limited than analysis results)
for row in ws.survey_rows(study_id, survey_id):
	print(row)

# Sensor samples (you'll probably want to handle this per-participant)
for row in ws.sensor_rows(study_id, 'passivelocation'):
	print(row)
```

### Roadmap

* Command-line utilities for downloading various datasets
* Inclusion in pypi
* Adding support for workspace, study, and survey endpoints
* Adding support for diary endpoint
* Possibly adding support for API Triggers
* Possibly adding support for wearables

### Acknowledgements

The development of this software was sponsored by the Defense Advanced Research Projects Agency of the United States of America. The information herein does not necessarily reflect the position or the policy of the Government. No official endorsement should be inferred.

Metricwire and Catalyst are trademarks of Metricwire, Inc. Metricwire, Inc does not endorse, sponsor, or maintain this project.

### Credits


