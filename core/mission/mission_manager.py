from core.mission.mission import Mission
from core.queue.mission_queue import MissionQueue
from core.mission.storage import MissionStorage


class MissionManager:

    def __init__(self):

        self.counter = 0

        self.missions = {}

        self.queue = MissionQueue()

        self.storage = MissionStorage()

        self.load_saved()



    def create(self, goal, goals):

        self.counter += 1

        mission = Mission(
            mission_id=self.counter,
            goal=goal,
            goals=goals
        )

        self.missions[mission.id] = mission

        self.queue.add(
            mission
        )

        self.save()

        return mission



    def get(self, mission_id):

        return self.missions.get(
            mission_id
        )



    def all(self):

        return list(
            self.missions.values()
        )



    def remove(self, mission_id):

        mission = self.missions.pop(
            mission_id,
            None
        )

        if mission:

            self.queue.remove(
                mission_id
            )

            self.save()

        return mission



    def start(self, mission):

        mission.start()

        self.save()

        return mission



    def next(self):

        return self.queue.next()



    def update(self, mission):

        mission.update_progress()

        if mission.progress >= 100:

            mission.complete()

        self.save()

        return mission.progress



    def complete(self, mission, result=None):

        mission.complete(
            result
        )

        self.queue.remove(
            mission.id
        )

        self.save()

        return mission



    def fail(self, mission, error=None):

        mission.fail(
            error
        )

        self.queue.remove(
            mission.id
        )

        self.save()

        return mission



    def summary(self, mission):

        mission.update_progress()

        return mission.to_dict()



    def queue_status(self):

        return {
            "waiting": self.queue.size(),
            "missions": [
                m.to_dict()
                for m in self.queue.all()
            ]
        }



    def save(self):

        self.storage.save(
            [
                mission.to_dict()
                for mission in self.missions.values()
            ]
        )



    def load_saved(self):

        data = self.storage.load()

        for item in data:

            mission = Mission(
                mission_id=item["id"],
                goal=item["goal"],
                goals=[]
            )

            mission.status = item.get(
                "status",
                Mission.PENDING
            )

            mission.progress = item.get(
                "progress",
                0.0
            )

            mission.result = item.get(
                "result"
            )

            mission.error = item.get(
                "error"
            )


            self.missions[mission.id] = mission


            if mission.id > self.counter:

                self.counter = mission.id


            if mission.status in [
                Mission.PENDING,
                Mission.RUNNING
            ]:

                self.queue.add(
                    mission
                )



    def recover(self):

        recovered = []

        queued_ids = [
            mission.id
            for mission in self.queue.all()
        ]


        for mission in self.all():

            if mission.status == Mission.RUNNING:

                mission.status = Mission.PENDING
                mission.progress = 0.0


                if mission.id not in queued_ids:

                    self.queue.add(
                        mission
                    )


                recovered.append(
                    mission
                )


        self.save()

        return recovered
