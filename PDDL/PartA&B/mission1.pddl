(define (problem lunar-mission-1)
    (:domain lunar)

    (:objects
        r1 - rover
        l1 - lander
        wp1 wp2 wp3 wp4 wp5 - waypoint
    )

    (:init
        ; Fixed landing choice: Lander 1 is at WP1 in Mission 1.
        (belongs-to r1 l1)
        (lander-at l1 wp1)
        (aboard r1 l1)
        (memory-free r1)
        (sample-slot-free r1)
        (lander-storage-free l1)
        
        ; Directed connections transcribed from Figure 2.
        (connected wp1 wp2)
        (connected wp1 wp4)
        (connected wp2 wp3)
        (connected wp4 wp3)
        (connected wp3 wp5)
        (connected wp5 wp1)
    )

    ; Goals require delivery to the specified lander, not acquisition alone.
    (:goal (and
        (image-saved l1 wp5)
        (scan-saved l1 wp3)
        (sample-stored l1 wp1)
    ))
)
