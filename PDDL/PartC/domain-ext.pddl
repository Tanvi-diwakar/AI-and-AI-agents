(define (domain lunar-extended)
    (:requirements :strips :typing)

    (:types rover lander waypoint astronaut)

    (:predicates
        ; Static facts: ownership, landing sites, and directed map edges.
        (belongs-to ?r - rover ?l - lander)
        (lander-at ?l - lander ?w - waypoint)
        (connected ?from - waypoint ?to - waypoint)

        ; An undeployed rover has aboard, but no rover-at fact.
        (aboard ?r - rover ?l - lander)
        (rover-at ?r - rover ?w - waypoint)

        ; One shared memory slot for both images and scans.
        (memory-free ?r - rover)
        (carrying-image ?r - rover ?w - waypoint)
        (carrying-scan ?r - rover ?w - waypoint)
        (image-saved ?l - lander ?w - waypoint)
        (scan-saved ?l - lander ?w - waypoint)

        ; Sample storage is independent of the data memory slot.
        (sample-slot-free ?r - rover)
        (carrying-sample ?r - rover ?origin - waypoint)
        (lander-storage-free ?l - lander)
        (sample-stored ?l - lander ?origin - waypoint)

        ; Each astronaut has an immutable owner and exactly one internal location.
        (astronaut-belongs-to ?a - astronaut ?l - lander)
        (in-docking-bay ?a - astronaut ?l - lander)
        (in-control-room ?a - astronaut ?l - lander)
    )

    ; Deployment creates the rover location and consumes its aboard status. The assigned astronaut must be in the required room.
    (:action deploy
        :parameters (?r - rover ?l - lander ?w - waypoint ?a - astronaut)
        :precondition (and
            (belongs-to ?r ?l)
            (aboard ?r ?l)
            (lander-at ?l ?w)
            (astronaut-belongs-to ?a ?l)
            (in-docking-bay ?a ?l)
        )
        :effect (and
            (rover-at ?r ?w)
            (not (aboard ?r ?l))
        )
    )

    ; Only an explicitly listed directed edge can be traversed.
    (:action move
        :parameters (?r - rover ?from - waypoint ?to - waypoint)
        :precondition (and
            (rover-at ?r ?from)
            (connected ?from ?to)
        )
        :effect (and
            (not (rover-at ?r ?from))
            (rover-at ?r ?to)
        )
    )

    ; Acquiring data occupies memory; it does not yet satisfy a saved-data goal.
    (:action capture-image
        :parameters (?r - rover ?w - waypoint)
        :precondition (and
            (rover-at ?r ?w)
            (memory-free ?r)
        )
        :effect (and
            (carrying-image ?r ?w)
            (not (memory-free ?r))
        )
    )

    ; Scans compete with images for the same memory slot.
    (:action perform-scan
        :parameters (?r - rover ?w - waypoint)
        :precondition (and
            (rover-at ?r ?w)
            (memory-free ?r)
        )
        :effect (and
            (carrying-scan ?r ?w)
            (not (memory-free ?r))
        )
    )

    ; Wireless transfer to the owning lander needs no co-location. The assigned astronaut must be in the required room.
    (:action transmit-image
        :parameters (?r - rover ?l - lander ?origin - waypoint ?a - astronaut)
        :precondition (and
            (belongs-to ?r ?l)
            (carrying-image ?r ?origin)
            (astronaut-belongs-to ?a ?l)
            (in-control-room ?a ?l)
        )
        :effect (and
            (image-saved ?l ?origin)
            (not (carrying-image ?r ?origin))
            (memory-free ?r)
        )
    )

    ; Only acquired data of the correct kind can be transmitted. The assigned astronaut must be in the required room.
    (:action transmit-scan
        :parameters (?r - rover ?l - lander ?origin - waypoint ?a - astronaut)
        :precondition (and
            (belongs-to ?r ?l)
            (carrying-scan ?r ?origin)
            (astronaut-belongs-to ?a ?l)
            (in-control-room ?a ?l)
        )
        :effect (and
            (scan-saved ?l ?origin)
            (not (carrying-scan ?r ?origin))
            (memory-free ?r)
        )
    )

    ; A sample records its source waypoint and occupies the rover sample slot.
    (:action collect-sample
        :parameters (?r - rover ?origin - waypoint)
        :precondition (and
            (rover-at ?r ?origin)
            (sample-slot-free ?r)
        )
        :effect (and
            (carrying-sample ?r ?origin)
            (not (sample-slot-free ?r))
        )
    )

    ; Physical delivery frees the rover slot and permanently fills the lander slot. The assigned astronaut must be in the required room.
    (:action store-sample
        :parameters (?r - rover ?l - lander ?origin - waypoint ?site - waypoint ?a - astronaut)
        :precondition (and
            (belongs-to ?r ?l)
            (carrying-sample ?r ?origin)
            (rover-at ?r ?site)
            (lander-at ?l ?site)
            (lander-storage-free ?l)
            (astronaut-belongs-to ?a ?l)
            (in-docking-bay ?a ?l)
        )
        :effect (and
            (sample-stored ?l ?origin)
            (not (carrying-sample ?r ?origin))
            (sample-slot-free ?r)
            (not (lander-storage-free ?l))
        )
    )

    ; Move between internal areas of the same owning lander.
    (:action go-to-control-room
        :parameters (?a - astronaut ?l - lander)
        :precondition (and
            (astronaut-belongs-to ?a ?l)
            (in-docking-bay ?a ?l)
        )
        :effect (and
            (in-control-room ?a ?l)
            (not (in-docking-bay ?a ?l))
        )
    )

    ; The source location is removed so an astronaut cannot be in both areas.
    (:action go-to-docking-bay
        :parameters (?a - astronaut ?l - lander)
        :precondition (and
            (astronaut-belongs-to ?a ?l)
            (in-control-room ?a ?l)
        )
        :effect (and
            (in-docking-bay ?a ?l)
            (not (in-control-room ?a ?l))
        )
    )
)
