from flask import Flask, render_template, request

app = Flask(__name__)

# База данных космодромов
launch_sites = {
    "Kennedy Space Center": {"location": "Florida, USA", "launch_cost": 5000000},
    "Baikonur Cosmodrome": {"location": "Kazakhstan", "launch_cost": 3000000},
    "Guiana Space Centre": {"location": "French Guiana", "launch_cost": 4000000},
}

# База данных ракетоносителей с указанием космодрома
rockets_db = {
    "Soyuz-2": {
        "max_payload_leo": 7020, "max_payload_geo": 1370, "cost_per_kg": 7000, "height": 46.1,
        "dry_mass": 308000, "specific_impulse": 310, "fuel_type": "керосин + жидкий кислород",
        "fuel_capacity": 90000, "oxidizer_capacity": 210000,
        "launch_site": "Baikonur Cosmodrome"
    },
    "Falcon 9": {
        "max_payload_leo": 22800, "max_payload_geo": 8300, "cost_per_kg": 4000, "height": 70,
        "dry_mass": 549054, "specific_impulse": 348, "fuel_type": "керосин RP-1 + жидкий кислород",
        "fuel_capacity": 115000, "oxidizer_capacity": 275000,
        "launch_site": "Kennedy Space Center"
    },
    "Ariane 5": {
        "max_payload_leo": 20000, "max_payload_geo": 10000, "cost_per_kg": 10000, "height": 51.8,
        "dry_mass": 780000, "specific_impulse": 430, "fuel_type": "жидкий водород + жидкий кислород",
        "fuel_capacity": 25000, "oxidizer_capacity": 150000,
        "launch_site": "Guiana Space Centre"
    },
    "Atlas V": {
        "max_payload_leo": 18800, "max_payload_geo": 8900, "cost_per_kg": 8000, "height": 58.3,
        "dry_mass": 334500, "specific_impulse": 338, "fuel_type": "керосин RP-1 + жидкий кислород",
        "fuel_capacity": 65000, "oxidizer_capacity": 155000,
        "launch_site": "Kennedy Space Center"
    },
    "Delta IV Heavy": {
        "max_payload_leo": 28790, "max_payload_geo": 14220, "cost_per_kg": 12000, "height": 71,
        "dry_mass": 733000, "specific_impulse": 420, "fuel_type": "жидкий водород + жидкий кислород",
        "fuel_capacity": 65000, "oxidizer_capacity": 390000,
        "launch_site": "Kennedy Space Center"
    },
    "Long March 5": {
        "max_payload_leo": 25000, "max_payload_geo": 14000, "cost_per_kg": 6000, "height": 56.97,
        "dry_mass": 869000, "specific_impulse": 430, "fuel_type": "жидкий водород + жидкий кислород",
        "fuel_capacity": 75000, "oxidizer_capacity": 450000,
        "launch_site": "Baikonur Cosmodrome"  # Для примера
    },
    "Proton-M": {
        "max_payload_leo": 23000, "max_payload_geo": 6920, "cost_per_kg": 6500, "height": 58.2,
        "dry_mass": 705000, "specific_impulse": 316, "fuel_type": "гидразин + тетроксид азота",
        "fuel_capacity": 230000, "oxidizer_capacity": 280000,
        "launch_site": "Baikonur Cosmodrome"
    },
    "SLS Block 1": {
        "max_payload_leo": 95000, "max_payload_geo": 26000, "cost_per_kg": 20000, "height": 98,
        "dry_mass": 2500000, "specific_impulse": 450, "fuel_type": "жидкий водород + жидкий кислород",
        "fuel_capacity": 300000, "oxidizer_capacity": 1800000,
        "launch_site": "Kennedy Space Center"
    }
}

# Защита полезной нагрузки
def get_payload_protection(apogee, perigee, inclination, payload_mass):
    global protection_mass, protection_cost, protection_percentage
    altitude = (apogee + perigee) / 2
    eccentricity = (apogee - perigee) / (apogee + perigee + 2 * 6371)

    if altitude >= 35786:
        protection = "Титановый корпус + многослойная радиационная защита (Pb/Al) + тепловой экран"
        mass_factor = 0.2
        cost_per_kg = 15000
    elif altitude > 2000:
        if eccentricity > 0.1:
            protection = "Алюминиевый корпус + усиленная радиационная защита + термостойкий слой"
            mass_factor = 0.15
            cost_per_kg = 10000
        else:
            protection = "Алюминиевый корпус + радиационная защита (Al)"
            mass_factor = 0.1
            cost_per_kg = 8000
    else:
        if inclination > 60:
            protection = "Алюминиевый корпус + защита от микрометеоритов + базовая радиационная защита"
            mass_factor = 0.08
            cost_per_kg = 6000
        else:protection = "Алюминиевый корпус + защита от микрометеоритов"
        mass_factor = 0.05
        cost_per_kg = 4000
        protection_mass = payload_mass * mass_factor
        protection_cost = protection_mass * cost_per_kg
        protection_percentage = mass_factor * 100
    return protection, protection_mass, protection_cost, protection_percentage

# Расчёт топлива
def calculate_fuel(rocket, payload_mass, protection_mass, apogee, perigee, inclination):
    g = 9.81
    isp = rocket["specific_impulse"]
    dry_mass = rocket["dry_mass"]
    total_mass = dry_mass + payload_mass + protection_mass

    altitude = (apogee + perigee) / 2
    eccentricity = (apogee - perigee) / (apogee + perigee + 2 * 6371)

    delta_v = 7500 if altitude <= 2000 else (9000 if altitude <= 20000 else 11000)
    if inclination > 60:
        delta_v += 200
    if eccentricity > 0.3:
        delta_v += 300

    mass_ratio = 2.71828 ** (delta_v / (isp * g))
    total_fuel_mass = total_mass * (mass_ratio - 1)

    max_total_fuel = rocket["fuel_capacity"] + rocket["oxidizer_capacity"]
    if total_fuel_mass > max_total_fuel:
        total_fuel_mass = max_total_fuel * 0.9

    print(f"Fuel calc for {rocket['name']}: Total fuel mass = {total_fuel_mass}, Delta-V = {delta_v}")

    if "керосин" in rocket["fuel_type"] or "RP-1" in rocket["fuel_type"]:
        fuel_ratio = 0.3
    elif "гидразин" in rocket["fuel_type"]:
        fuel_ratio = 0.45
    else:
        fuel_ratio = 0.15

    fuel_mass = total_fuel_mass * fuel_ratio
    oxidizer_mass = total_fuel_mass * (1 - fuel_ratio)

    max_fuel = rocket["fuel_capacity"]
    max_oxidizer = rocket["oxidizer_capacity"]
    if fuel_mass > max_fuel or oxidizer_mass > max_oxidizer:
        print(f"Fuel check failed: Fuel={fuel_mass}/{max_fuel}, Oxidizer={oxidizer_mass}/{max_oxidizer}")
        return None, None, None

    fuel_cost = total_fuel_mass * 5
    return fuel_mass, oxidizer_mass, fuel_cost

# Выбор ракетоносителя
def find_best_rocket(payload_mass, apogee, perigee, inclination):
    try:
        altitude = (apogee + perigee) / 2
        orbit_type = "LEO" if altitude <= 2000 else ("MEO" if altitude <= 20000 else "GEO")
        eccentricity = (apogee - perigee) / (apogee + perigee + 2 * 6371)

        print(f"Altitude: {altitude}, Orbit: {orbit_type}, Payload: {payload_mass}, Adjusted: {payload_mass + payload_mass * 0.05}")

        # Обернем вызов get_payload_protection в try-except
        try:
            protection, protection_mass, protection_cost, protection_percentage = get_payload_protection(apogee, perigee, inclination, payload_mass)
        except Exception as e:
            print(f"Ошибка в get_payload_protection: {e}")
            return {
                "name": f"Ошибка в расчете защиты: {str(e)}",
                "cost": 0,
                "protection": "N/A",
                "protection_mass": 0,
                "protection_cost": 0,
                "protection_percentage": 0,
                "fuel_mass": 0,
                "oxidizer_mass": 0,
                "fuel_type": "N/A",
                "launch_site": "N/A",
                "launch_site_cost": 0,
                "launch_site_location": "N/A"
            }

        total_payload = payload_mass + protection_mass
        payload_adjustment = 1.0 + (0.03 if inclination > 60 else 0) + (0.05 if eccentricity > 0.3 else 0)
        adjusted_payload = total_payload * payload_adjustment

        print(f"Adjusted payload: {adjusted_payload}")

        best_rocket = None
        min_total_cost = float('inf')
        best_payload_diff = float('inf')

        for name, data in rockets_db.items():
            data["name"] = name
            max_payload = data["max_payload_geo"] if orbit_type == "GEO" else data["max_payload_leo"]
            print(f"Checking {name}: Max payload {max_payload} vs {adjusted_payload}")
            if max_payload >= adjusted_payload:
                fuel_mass, oxidizer_mass, fuel_cost = calculate_fuel(data, payload_mass, protection_mass, apogee, perigee, inclination)
                if fuel_mass is None:
                    print(f"{name} failed fuel check")
                    continue
                payload_cost = payload_mass * data["cost_per_kg"]
                launch_site = data["launch_site"]
                launch_site_cost = launch_sites[launch_site]["launch_cost"]
                total_cost = payload_cost + fuel_cost + protection_cost + launch_site_cost
                payload_diff = abs(max_payload - adjusted_payload)

                score = 0.7 * (payload_diff / max_payload) + 0.3 * (total_cost / 1000000)
                if score < min_total_cost or (score == min_total_cost and payload_diff < best_payload_diff):
                    min_total_cost = score
                    best_payload_diff = payload_diff
                    best_rocket = {
                        "name": name,
                        "cost": total_cost,
                        "protection": protection,
                        "protection_mass": protection_mass,
                        "protection_cost": protection_cost,
                        "protection_percentage": protection_percentage,
                        "fuel_mass": fuel_mass,
                        "oxidizer_mass": oxidizer_mass,
                        "fuel_type": data["fuel_type"],
                        "launch_site": launch_site,
                        "launch_site_cost": launch_site_cost,
                        "launch_site_location": launch_sites[launch_site]["location"]
                    }
                    print(f"New best: {name}, Cost: {total_cost}, Payload diff: {payload_diff}, Score: {score}")

        if best_rocket and best_rocket["name"] == "Falcon 9" and payload_mass < 8000:
            best_rocket = None
        if best_rocket and best_rocket["name"] == "SLS Block 1" and payload_mass < 30000:
            best_rocket = None

        if best_rocket is None:
            print("No suitable rocket found")
            return {
                "name": "Нет подходящего носителя",
                "cost": 0,
                "protection": "N/A",
                "protection_mass": 0,
                "protection_cost": 0,
                "protection_percentage": 0,
                "fuel_mass": 0,
                "oxidizer_mass": 0,
                "fuel_type": "N/A",
                "launch_site": "N/A",
                "launch_site_cost": 0,
                "launch_site_location": "N/A"
            }
        return best_rocket
    except Exception as e:
        print(f"Ошибка в find_best_rocket: {e}")
        return {
            "name": f"Ошибка в выборе ракетоносителя: {str(e)}",
            "cost": 0,
            "protection": "N/A",
            "protection_mass": 0,
            "protection_cost": 0,
            "protection_percentage": 0,
            "fuel_mass": 0,
            "oxidizer_mass": 0,
            "fuel_type": "N/A",
            "launch_site": "N/A",
            "launch_site_cost": 0,
            "launch_site_location": "N/A"
        }

# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            payload_mass_str = request.form.get('payload_mass')
            orbit_type = request.form.get('orbit_type')
            apogee_str = request.form.get('apogee', '0')
            perigee_str = request.form.get('perigee', '0')
            inclination_str = request.form.get('inclination', '0')

            # Преобразуем строки в числа и проверяем корректность
            try:
                payload_mass = float(payload_mass_str) if payload_mass_str else 0
            except (ValueError, TypeError):
                raise ValueError("Масса полезной нагрузки должна быть числом")

            try:
                apogee = float(apogee_str) if apogee_str else 0
            except (ValueError, TypeError):
                raise ValueError("Апогей должен быть числом")

            try:
                perigee = float(perigee_str) if perigee_str else 0
            except (ValueError, TypeError):raise ValueError("Перигей должен быть числом")

            try:
                inclination = float(inclination_str) if inclination_str else 0
            except (ValueError, TypeError):
                raise ValueError("Наклонение должно быть числом")

            print(f"Input: Payload={payload_mass}, Apogee={apogee}, Perigee={perigee}, Incl={inclination}, Orbit={orbit_type}")

            # Проверяем тип орбиты и задаем значения по умолчанию
            if orbit_type in ["LEO", "MEO", "GEO"]:
                altitude_map = {"LEO": 500, "MEO": 10000, "GEO": 35786}
                apogee = altitude_map[orbit_type]
                perigee = altitude_map[orbit_type]
                inclination = 0 if orbit_type == "GEO" else 28.5
            elif apogee <= 0 or perigee <= 0:
                result = {
                    "name": "Ошибка: Укажите корректные апогей и перигей (оба должны быть больше 0)",
                    "cost": 0,
                    "protection": "N/A",
                    "protection_mass": 0,
                    "protection_cost": 0,
                    "protection_percentage": 0,
                    "fuel_mass": 0,
                    "oxidizer_mass": 0,
                    "fuel_type": "N/A",
                    "launch_site": "N/A",
                    "launch_site_cost": 0,
                    "launch_site_location": "N/A"
                }
                return render_template('index.html', result=result, rockets=rockets_db, launch_sites=launch_sites)

            # Проверяем массу полезной нагрузки
            if payload_mass <= 0:
                result = {
                    "name": "Ошибка: Масса полезной нагрузки должна быть больше 0",
                    "cost": 0,
                    "protection": "N/A",
                    "protection_mass": 0,
                    "protection_cost": 0,
                    "protection_percentage": 0,
                    "fuel_mass": 0,
                    "oxidizer_mass": 0,
                    "fuel_type": "N/A",
                    "launch_site": "N/A",
                    "launch_site_cost": 0,
                    "launch_site_location": "N/A"
                }
                return render_template('index.html', result=result, rockets=rockets_db, launch_sites=launch_sites)

            # Вызываем функцию выбора ракетоносителя
            result = find_best_rocket(payload_mass, apogee, perigee, inclination)

        except Exception as e:
            print(f"Ошибка в обработке запроса: {e}")
            result = {
                "name": f"Ошибка ввода: {str(e)}",
                "cost": 0,
                "protection": "N/A",
                "protection_mass": 0,
                "protection_cost": 0,
                "protection_percentage": 0,
                "fuel_mass": 0,
                "oxidizer_mass": 0,
                "fuel_type": "N/A",
                "launch_site": "N/A",
                "launch_site_cost": 0,
                "launch_site_location": "N/A"
            }

    return render_template('index.html', result=result, rockets=rockets_db, launch_sites=launch_sites)

if __name__ == '__main__':
    app.run(debug=True)