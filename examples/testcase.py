all_testcases = [
    {
        "field": {
            "field_width": 220,
            "field_height": 220,
            "obstacle_specs": [
                (80, 65, 60, 20),  # Obstacle 1
                (40, 120, 70, 20),  # Obstacle 2
                (20, 10, 40, 20),  # Obstacle 3 (near boundary)
            ],
            "name": "Small Field",
        },
        "params": {
            # Đề xuất tối ưu cho field 220x220m với obstacles 20m cao
            "operating_width": 6.0,        # 6m: cân bằng giữa số lượng track (~37) và độ chính xác
            "turning_radius": 5.0,          # 5m: đủ lớn để quay mượt, gần bằng operating_width
            "num_headland_passes": 2,       # 2 passes: đủ không gian quay cho đồng lớn
            "driving_direction": 0.0,       # 0° (ngang): tối ưu vì obstacles cao 20m < rộng 40-70m
            "obstacle_threshold": 0,    # 25m: lớn hơn height obstacles (20m) để không bỏ sót
        },
        "aco": {
            "alpha": 1.0,           # Ảnh hưởng pheromone
            "beta": 2.0,            # Ảnh hưởng heuristic (ưu tiên khoảng cách ngắn)
            "rho": 0.1,             # Tỷ lệ bay hơi pheromone
            "q": 100.0,             # Hằng số cường độ pheromone
            "num_iterations": 100,  # Số lần lặp cho field nhỏ
            "elitist_weight": 2.0,  # Trọng số cho giải pháp tốt nhất
        }
    },
    {
        "field": {
            "field_width": 700, #350,
            "field_height": 350, #700,
            "obstacle_specs": [
                (70, 220, 100, 60),
                (320, 150, 110, 90),
                (530, 200, 120, 70)
            ],
            "name": "Medium Field",
        },
        "params": {
            "operating_width": 6.0,      
            "turning_radius": 5.0,  
            "num_headland_passes": 2,
            "driving_direction": 0.0,
            "obstacle_threshold": 0,  # Tăng lên cho obstacles lớn hơn (60-90m)
        },
        "aco": {
            "alpha": 1.0,           # Ảnh hưởng pheromone
            "beta": 2.5,            # Tăng ảnh hưởng heuristic cho field lớn hơn
            "rho": 0.15,            # Tăng tỷ lệ bay hơi để tìm kiếm tốt hơn
            "q": 150.0,             # Tăng cường độ pheromone
            "num_iterations": 150,  # Tăng số lần lặp cho field trung bình
            "elitist_weight": 2.5,  # Tăng trọng số elite
        }
    },
    {
        "field": {
            "field_width": 857, #350,
            "field_height": 659, #700,
            "obstacle_specs": [
                (70, 320, 130, 90),
                (300, 320, 100, 70),
                (530, 450, 120, 100),
                (700, 180, 80, 110)
            ],
            "name": "Large Field",
        },
        "params": {
            "operating_width": 6.0,      
            "turning_radius": 5.0,  
            "num_headland_passes": 3,    # Tăng lên 3 passes cho field lớn
            "driving_direction": 0.0,
            "obstacle_threshold": 0,  # Tăng lên cho obstacles lớn (70-110m)
        },
        "aco": {
            "alpha": 1.2,           # Tăng ảnh hưởng pheromone
            "beta": 3.0,            # Tăng mạnh ảnh hưởng heuristic
            "rho": 0.2,             # Tăng bay hơi để khám phá rộng hơn
            "q": 200.0,             # Tăng cường độ pheromone cho field lớn
            "num_iterations": 200,  # Tăng số lần lặp cho field lớn
            "elitist_weight": 3.0,  # Tăng trọng số elite
        }
    }
]

testcase = all_testcases[0]