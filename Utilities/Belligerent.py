class Belligerent:
    def __init__(self, speed: int):
        self.attack = 0
        self.max_hp = 500
        self.speed = speed
        self.cooldown = 1000


    def __str__(self) -> str:
        return str(self.speed)

    
    def __lt__(self, other: "Belligerent"):
        if not isinstance(other, Belligerent):
            raise TypeError
        return self.cooldown < other.cooldown
    

def set_next_actor(player1, player2):
    while min(player1, player2).cooldown > 0:
        player1.cooldown -= player1.speed
        player2.cooldown -= player2.speed
    actor = min(player1, player2)
    actor.cooldown = 1000
    return actor


class BaseStatus:
    def __init__(self, target: Belligerent, duration: int):
        self.target = target
        self.counter = duration

    def on_application(self):
        pass

    def on_turn(self):
        self.counter -= 1

    def on_remove(self):
        pass

class Slow(BaseStatus):
    def __init__(self, amount: int, **kwargs):
        self.amount = amount
        super().__init__(**kwargs)

    def on_application(self):
        self.target.speed -= self.amount
        return super().on_application()
    
    def on_remove(self):
        self.target.speed += self.amount
        return super().on_remove()
    

if __name__ == "__main__":
    x = Belligerent(16)
    y = Belligerent(34)

    # for _ in range(5):
    #     print(set_next_actor(x, y), x.cooldown, y.cooldown)

    status = Slow(5, target=x, duration=2)
    print(status.__dict__)