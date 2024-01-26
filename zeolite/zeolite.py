#!/usr/bin/env python

# Copyright (c) 2024 Board of Regents of the University of Wisconsin System
# Written by Nate Vack <njvack@wisc.edu>
# Code contributions from Yogesh Prabhu <yprabhu2@wisc.edu>

"""
Shared facilities for the MetricWire Consumer API:

https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0

Provides features such as:

* OAuth2 authentication
* Enumerating users
* Downloading Survey data
* Downloading media (video / photo) data
* Downloading Analysis data
* Downloading Sensor data

Does not currently support creating API triggers.

In addition, different API endpoints return data in different formats -- for
example, one endpoint may have "userid" and another may have "User.ID." This
module does not attempt to normalize the data; you'll need to do that yourself.

"""

import requests

# Our logger will log WARNINGS by default, override this in scripts
import logging

logging.basicConfig(format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


STANDARD_HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}

MW_API_URL = "https://consumer-api.metricwire.com"


class Metricwire:
    def __init__(self, workspace_id, client_id, client_secret, api_url=MW_API_URL):
        self.workspace_id = workspace_id
        self.api_url = api_url
        self.session = self._get_authenticated_session(client_id, client_secret)

    def _get_authenticated_session(self, client_id, client_secret):
        """
        OAuth2 client credentials authentication. Returns a requests.Session
        """
        url = f"{self.api_url}/oauth/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        response = requests.post(url, data=params, headers=STANDARD_HEADERS)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        logger.debug("Authenticated successfully, have access token!")
        s = requests.Session()
        s.headers.update(STANDARD_HEADERS)
        s.headers.update({"Authorization": f"Bearer {access_token}"})
        return s

    def _get_skip_results(self, base_url, method="GET"):
        """
        Internal method -- yields a generator that will yield successive pages of
        results from the API with increasing skip numbers. This method does not
        pull the "submissions" key out from the results; it returns the entire
        parsed JSON structure.

        Raises an error if the HTTP response code is not 200.
        """
        skip = 0
        while True:
            url = f"{base_url}/{skip}"
            logger.debug(f"Getting {url} woth method {method}")
            response = self.session.request(method, url)
            response.raise_for_status()
            parsed = response.json()
            logger.debug(f"Got {len(parsed['submissions'])} submissions")
            if len(parsed["submissions"]) == 0:
                break
            yield parsed
            skip += 1

    def _get_submissions_rowiter(self, base_url, method="GET"):
        """
        Internal method. Returns an iterator for all individual rows from the
        "submissions" part of an API response. Useful for either writing to
        CSV, or loading into a dataframe.
        """
        for result in self._get_skip_results(base_url, method):
            for row in result["submissions"]:
                yield row

    def analysis_rows(self, analysis_id):
        """
        Return an iterator for all analysis results as dicts.
        """
        url = f"{self.api_url}/analysis/{self.workspace_id}/{analysis_id}"
        return self._get_submissions_rowiter(url, "POST")

    def media_rows(self, study_id, survey_id):
        """
        Return an iterator for all media submissions (photos, videos)
        for a given survey as dicts.
        """
        url = f"{self.api_url}/submissions/media/{self.workspace_id}/{study_id}/{survey_id}"
        return self._get_submissions_rowiter(url)

    def submissions_rows(self, study_id, survey_id):
        """
        Return an iterator for all submissions as dicts for a given survey.
        """
        url = f"{self.api_url}/submissions/{self.workspace_id}/{study_id}/{survey_id}"
        return self._get_submissions_rowiter(url)

    def participants_rows(self, study_id):
        """
        Returns a list dicts for all participants in a given study.
        Frustratingly, not each participant will necessarily have the same
        keys. If you want to pass this to a csv.DictWriter, you'll need to make
        a set of all the keys and use it as fieldnames.
        """
        url = f"{self.api_url}/participants/{self.workspace_id}/{study_id}"
        logger.debug(f"Getting {url}")
        result = self.session.get(url)
        result.raise_for_status()
        ppt_list = result.json()
        return ppt_list

    def sensor_rows(self, study_id, sensor_type, user_ids=None):
        """
        Return an iterator for all sensor days as dicts for a study. The rows
        will be in batches of at most size limit.

        sensor_type is documented here:
        https://app.swaggerhub.com/apis-docs/MetricWire/ConsumerAPI/3.0.0#/Sensors/GetSensorSubmissionsFromStudyEnterprise

        As far as I know, the only implemented type is "passivelocation"

        User_ids can be an array of MetricWire user IDs (see participants_rows()
        to get a complete list for your study) or None to download everyone's
        data.
        """
        url = f"{self.api_url}/sensordata/{sensor_type}/{self.workspace_id}/{study_id}"
        if user_ids is None:
            ppt_list = self.participants_rows(study_id)
            user_ids = [p["userId"] for p in ppt_list if "userId" in p]
        logger.debug(f"User list: {user_ids}")
        BATCH_SIZE = 10000
        for user_id in user_ids:
            page = 0
            form_data = {
                "limit": BATCH_SIZE,
                "userId": user_id,
            }
            while True:
                skip = page * BATCH_SIZE
                form_data["skip"] = skip
                logger.debug(f"Posting to {url}")

                response = self.session.post(url, data=form_data)
                response.raise_for_status()
                resp_json = response.json()
                data_rows = resp_json["data"]
                if len(data_rows) == 0:
                    break
                for row in data_rows:
                    yield row
                page = page + 1


if __name__ == "__main__":
    """
    Just some light testing
    """
    import pandas as pd
    import os
    import sys

    logger.setLevel(logging.DEBUG)
    mw = Metricwire(
        "6480ea4aa4c006f315e1d5a5",
        os.environ["MW_CLIENT_ID"],
        os.environ["MW_CLIENT_SECRET"],
    )

    rows = mw.participants_rows("6536d75957b62ae525b9cf76")
    ppt_df = pd.DataFrame(rows, dtype=str)
    ppt_df.to_csv(sys.stdout, index=False)

    all_rows = [
        row for row in mw.sensor_rows("6536d75957b62ae525b9cf76", "passivelocation")
    ]
    print(len(all_rows))
