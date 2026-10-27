(define (domain lunar)
    (:requirements :strips :typing)

    (:types rover lander waypoint)

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
    )

    ; Deployment creates the rover location and consumes its aboard status.
    (:action deploy
        :parameters (?r - rover ?l - lander ?w - waypoint)
        :precondition (and
            (belongs-to ?r ?l)
            (aboard ?r ?l)
            (lander-at ?l ?w)
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

    ; Wireless transfer to the owning lander needs no co-location.
    (:action transmit-image
        :parameters (?r - rover ?l - lander ?origin - waypoint)
        :precondition (and
            (belongs-to ?r ?l)
            (carrying-image ?r ?origin)
        )
        :effect (and
            (image-saved ?l ?origin)
            (not (carrying-image ?r ?origin))
            (memory-free ?r)
        )
    )

    ; Only acquired data of the correct kind can be transmitted.
    (:action transmit-scan
        :parameters (?r - rover ?l - lander ?origin - waypoint)
        :precondition (and
            (belongs-to ?r ?l)
            (carrying-scan ?r ?origin)
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

    ; Physical delivery frees the rover slot and permanently fills the lander slot.
    (:action store-sample
        :parameters (?r - rover ?l - lander ?origin - waypoint ?site - waypoint)
        :precondition (and
            (belongs-to ?r ?l)
            (carrying-sample ?r ?origin)
            (rover-at ?r ?site)
            (lander-at ?l ?site)
            (lander-storage-free ?l)
        )
        :effect (and
            (sample-stored ?l ?origin)
            (not (carrying-sample ?r ?origin))
            (sample-slot-free ?r)
            (not (lander-storage-free ?l))
        )
    )
)
