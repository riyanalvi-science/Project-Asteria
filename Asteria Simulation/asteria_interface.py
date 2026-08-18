class AsteriaInterface:

    def __init__(self, brain):

        self.brain = brain


    def update_sensors(self, sensor_data):

        environment = (
            self.brain.environment_analyzer.environment
        )


        environment.update_front_distance(
            sensor_data.get("front", 1000)
            if sensor_data.get("front") is not None
            else 1000
        )


        environment.update_rear_distance(
            sensor_data.get("rear", 1000)
            if sensor_data.get("rear") is not None
            else 1000
        )


        environment.update_left_distance(
            sensor_data.get("left", 1000)
            if sensor_data.get("left") is not None
            else 1000
        )


        environment.update_right_distance(
            sensor_data.get("right", 1000)
            if sensor_data.get("right") is not None
            else 1000
        )



    def run_cycle(self):

        result = self.brain.run_cycle()

        return result