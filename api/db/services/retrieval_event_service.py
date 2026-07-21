#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import uuid

from peewee import fn

from api.db.db_models import RetrievalEvent
from api.db.services.common_service import CommonService


class RetrievalEventService(CommonService):
    model = RetrievalEvent

    @classmethod
    def record(cls, **kwargs):
        kwargs["id"] = uuid.uuid4().hex
        return cls.insert(**kwargs)

    @classmethod
    def stats(cls, tenant_id, from_date, to_date):
        day = fn.DATE_FORMAT(RetrievalEvent.create_date, "%Y-%m-%d").alias("day")
        query = (
            RetrievalEvent.select(
                day,
                RetrievalEvent.caller_type,
                fn.COUNT(RetrievalEvent.id).alias("requests"),
                fn.SUM(RetrievalEvent.status == "success").alias("successes"),
                fn.SUM(RetrievalEvent.result_count == 0).alias("empty_results"),
                fn.AVG(RetrievalEvent.latency).alias("avg_latency"),
                fn.MAX(RetrievalEvent.latency).alias("max_latency"),
                fn.AVG(RetrievalEvent.result_count).alias("avg_result_count"),
                fn.AVG(RetrievalEvent.top_similarity).alias("avg_top_similarity"),
            )
            .where(
                RetrievalEvent.tenant_id == tenant_id,
                RetrievalEvent.create_date.between(from_date, to_date),
            )
            .group_by(day, RetrievalEvent.caller_type)
            .order_by(day, RetrievalEvent.caller_type)
        )
        return [
            {
                "day": row.day,
                "caller_type": row.caller_type,
                "requests": row.requests,
                "successes": row.successes or 0,
                "empty_results": row.empty_results or 0,
                "avg_latency": float(row.avg_latency or 0),
                "max_latency": float(row.max_latency or 0),
                "avg_result_count": float(row.avg_result_count or 0),
                "avg_top_similarity": float(row.avg_top_similarity) if row.avg_top_similarity is not None else None,
            }
            for row in query
        ]