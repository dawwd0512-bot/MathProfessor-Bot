from collections import deque


class MissionQueue:

    def __init__(self):

        self.queue = deque()


    def add(self, mission):

        self.queue.append(mission)

        return mission


    def next(self):

        if not self.queue:
            return None

        return self.queue.popleft()


    def peek(self):

        if not self.queue:
            return None

        return self.queue[0]


    def remove(self, mission_id):

        for mission in list(self.queue):

            if mission.id == mission_id:

                self.queue.remove(mission)

                return mission

        return None


    def size(self):

        return len(self.queue)


    def clear(self):

        self.queue.clear()


    def all(self):

        return list(self.queue)
