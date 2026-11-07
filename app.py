
from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import date

app = Flask(__name__)
app.secret_key = "metalpro-secret-key"

DATA_DIR = "data"


# ==============================
# FUNGSI DATA JSON
# ==============================

def load_data(filename):
    path = os.path.join(DATA_DIR, filename)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(filename, data):
    path = os.path.join(DATA_DIR, filename)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def next_id(data):
    return max([item["id"] for item in data], default=0) + 1


# ==============================
# PERHITUNGAN OEE
# ==============================

def calculate_oee(production):
    if not production:
        return 0, 0, 0, 0

    planned = sum(item["planned_time"] for item in production)
    downtime = sum(item["downtime"] for item in production)
    target = sum(item["target"] for item in production)
    actual = sum(item["actual"] for item in production)
    defects = sum(item["defects"] for item in production)

    availability = (
        max(0, planned - downtime) / planned * 100
        if planned > 0 else 0
    )

    performance = (
        min(actual / target, 1) * 100
        if target > 0 else 0
    )

    quality = (
        max(0, actual - defects) / actual * 100
        if actual > 0 else 0
    )

    oee = availability * performance * quality / 10000

    return (
        round(availability, 2),
        round(performance, 2),
        round(quality, 2),
        round(oee, 2)
    )


# ==============================
# FORECASTING
# ==============================

def forecast_demand(sales):
    if len(sales) < 2:
        return []

    x = list(range(len(sales)))
    y = [item["demand"] for item in sales]

    n = len(sales)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    denominator = sum((xi - mean_x) ** 2 for xi in x)

    if denominator == 0:
        return []

    slope = sum(
        (xi - mean_x) * (yi - mean_y)
        for xi, yi in zip(x, y)
    ) / denominator

    intercept = mean_y - slope * mean_x

    return [
        max(0, round(intercept + slope * (n + i)))
        for i in range(3)
    ]


# ==============================
# DASHBOARD
# ==============================

@app.route("/")
def dashboard():
    inventory = load_data("inventory.json")
    machines = load_data("machines.json")
    production = load_data("production.json")

    availability, performance, quality, oee = calculate_oee(production)

    total_actual = sum(item["actual"] for item in production)
    total_defects = sum(item["defects"] for item in production)

    active_machines = sum(
        1 for item in machines
        if item["status"] == "Beroperasi"
    )

    low_stock = sum(
        1 for item in inventory
        if item["stock"] <= item["min_stock"]
    )

    return render_template(
        "dashboard.html",
        title="Dashboard",
        inventory=inventory,
        machines=machines,
        production=production,
        total_actual=total_actual,
        total_defects=total_defects,
        active_machines=active_machines,
        low_stock=low_stock,
        oee=oee,
        today=date.today().strftime("%d-%m-%Y")
    )


# ==============================
# INVENTORY
# ==============================

@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    items = load_data("inventory.json")

    if request.method == "POST":
        new_item = {
            "id": next_id(items),
            "name": request.form["name"].strip(),
            "category": request.form["category"],
            "stock": int(request.form["stock"]),
            "unit": request.form["unit"].strip(),
            "min_stock": int(request.form["min_stock"])
        }

        items.append(new_item)
        save_data("inventory.json", items)

        flash("Bahan berhasil ditambahkan.", "success")
        return redirect(url_for("inventory"))

    return render_template(
        "inventory.html",
        title="Manajemen Inventory",
        inventory=items
    )


@app.route("/inventory/update/<int:item_id>", methods=["POST"])
def update_inventory(item_id):
    items = load_data("inventory.json")

    for item in items:
        if item["id"] == item_id:
            item["stock"] = int(request.form["stock"])
            item["min_stock"] = int(request.form["min_stock"])
            break

    save_data("inventory.json", items)
    flash("Stok berhasil diperbarui.", "success")

    return redirect(url_for("inventory"))


@app.route("/inventory/delete/<int:item_id>", methods=["POST"])
def delete_inventory(item_id):
    items = load_data("inventory.json")

    items = [
        item for item in items
        if item["id"] != item_id
    ]

    save_data("inventory.json", items)
    flash("Bahan berhasil dihapus.", "success")

    return redirect(url_for("inventory"))


# ==============================
# DATA MESIN
# ==============================

@app.route("/machines", methods=["GET", "POST"])
def machines():
    items = load_data("machines.json")

    if request.method == "POST":
        new_machine = {
            "id": next_id(items),
            "name": request.form["name"].strip(),
            "process": request.form["process"].strip(),
            "status": request.form["status"]
        }

        items.append(new_machine)
        save_data("machines.json", items)

        flash("Mesin berhasil ditambahkan.", "success")
        return redirect(url_for("machines"))

    return render_template(
        "machines.html",
        title="Manajemen Mesin",
        machines=items
    )


@app.route("/machines/status/<int:machine_id>", methods=["POST"])
def update_machine_status(machine_id):
    items = load_data("machines.json")

    for item in items:
        if item["id"] == machine_id:
            item["status"] = request.form["status"]
            break

    save_data("machines.json", items)
    flash("Status mesin berhasil diperbarui.", "success")

    return redirect(url_for("machines"))


# ==============================
# PRODUKSI
# ==============================

@app.route("/production", methods=["GET", "POST"])
def production():
    records = load_data("production.json")
    machines = load_data("machines.json")

    if request.method == "POST":
        target = int(request.form["target"])
        actual = int(request.form["actual"])
        defects = int(request.form["defects"])
        planned_time = float(request.form["planned_time"])
        downtime = float(request.form["downtime"])

        if (
            target <= 0
            or actual < 0
            or actual > target
            or defects < 0
            or defects > actual
            or planned_time <= 0
            or downtime < 0
            or downtime > planned_time
        ):
            flash("Data produksi tidak valid. Periksa kembali input.", "error")
            return redirect(url_for("production"))

        if not any(
            item["id"] == int(request.form["machine_id"])
            for item in machines
        ):
            flash("Mesin tidak ditemukan.", "error")
            return redirect(url_for("production"))

        new_record = {
            "id": next_id(records),
            "date": request.form["date"],
            "product": request.form["product"].strip(),
            "machine_id": int(request.form["machine_id"]),
            "target": target,
            "actual": actual,
            "defects": defects,
            "planned_time": planned_time,
            "downtime": downtime
        }

        records.append(new_record)
        save_data("production.json", records)

        flash("Data produksi berhasil disimpan.", "success")
        return redirect(url_for("production"))

    machine_names = {
        str(item["id"]): item["name"]
        for item in machines
    }

    return render_template(
        "production.html",
        title="Data Produksi",
        production=records,
        machines=machines,
        machine_names=machine_names,
        today=date.today().isoformat()
    )


# ==============================
# ANALISIS PRODUKSI
# ==============================

@app.route("/analysis")
def analysis():
    production = load_data("production.json")
    sales = load_data("sales.json")

    availability, performance, quality, oee = calculate_oee(production)
    forecast = forecast_demand(sales)

    forecast_labels = (
        [item["month"] for item in sales]
        + ["Periode +1", "Periode +2", "Periode +3"]
    )

    forecast_values = (
        [item["demand"] for item in sales]
        + [None] * 3
    )

    forecast_line = (
        [None] * (len(sales) - 1)
        + ([sales[-1]["demand"]] if sales else [])
        + forecast
    )

    return render_template(
        "analysis.html",
        title="Analisis Produksi",
        availability=availability,
        performance=performance,
        quality=quality,
        oee=oee,
        sales=sales,
        forecast=forecast,
        forecast_labels=forecast_labels,
        forecast_values=forecast_values,
        forecast_line=forecast_line
    )


if __name__ == "__main__":
    app.run(debug=True)
