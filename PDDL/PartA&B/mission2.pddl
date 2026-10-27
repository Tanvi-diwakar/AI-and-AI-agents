(define (problem lunar-mission-2)
    (:domain lunar)

    (:objects
        r1 r2 - rover
        l1 l2 - lander
        wp1 wp2 wp3 wp4 wp5 wp6 - waypoint
    )

    (:init
        ; Lander 1 is fixed at WP2. Chosen landing site for Lander 2: WP1.
        (belongs-to r1 l1)
        (lander-at l1 wp2)
        (rover-at r1 wp2)
        (memory-free r1)
        (sample-slot-free r1)
        (lander-storage-free l1)
        
        (belongs-to r2 l2)
        (lander-at l2 wp1)
        (aboard r2 l2)
        (memory-free r2)
        (sample-slot-free r2)
        (lander-storage-free l2)
        
        ; Directed connections transcribed from Figure 3.
        (connected wp1 wp2)
        (connected wp2 wp1)
        (connected wp2 wp3)
        (connected wp2 wp4)
        (connected wp4 wp2)
        (connected wp3 wp5)
        (connected wp5 wp3)
        (connected wp5 wp6)
        (connected wp6 wp4)
    )

    ; Goals require delivery to the specified lander, not acquisition alone.
    (:goal (and
        (image-saved l1 wp3)
        (scan-saved l2 wp4)
        (image-saved l2 wp2)
        (scan-saved l1 wp6)
        (sample-stored l1 wp5)
        (sample-stored l2 wp1)
    ))
)
