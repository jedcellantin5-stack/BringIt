const day = document.getElementById("day");
const subject = document.getElementById("subject");
const addSubject = document.getElementById("addSubject");
const subjectList = document.getElementById("subjectList");
const selectedDay = document.getElementById("selectedDay");
const generate = document.getElementById("generate");
const checklist = document.getElementById("checklist");

const statusMessage = document.getElementById("statusMessage");

function showStatus(message) {

    statusMessage.textContent = message;
    statusMessage.style.display = "block";

}

let schedules = {
    Monday: [],
    Tuesday: [],
    Wednesday: [],
    Thursday: [],
    Friday: []
};


function displaySubjects() {

    subjectList.innerHTML = "";

    schedules[day.value].forEach(function (subjectName, index) {

        const li = document.createElement("li");

        li.textContent = subjectName + " ";

        const deleteButton = document.createElement("button");

        deleteButton.textContent = "🗑️";
        deleteButton.classList.add("delete-btn");

        deleteButton.addEventListener("click", function () {

            schedules[day.value].splice(index, 1);

            displaySubjects();

        });

        li.appendChild(deleteButton);

        subjectList.appendChild(li);

    });

}


/* SCHEDULE TYPE */

const scheduleTypes = document.querySelectorAll(
    'input[name="scheduleType"]'
);

const daySelector = document.getElementById("daySelector");
const weekSelector = document.getElementById("weekSelector");


scheduleTypes.forEach(function (radio) {

    radio.addEventListener("change", function () {

        if (radio.value === "week") {

            daySelector.style.display = "none";
            weekSelector.style.display = "block";

        }

        if (radio.value === "day") {

            daySelector.style.display = "block";
            weekSelector.style.display = "none";

        }

    });

});


/* DEFAULT */

daySelector.style.display = "none";
weekSelector.style.display = "block";


/* CHANGE DAY */

day.addEventListener("change", function () {

    selectedDay.textContent = day.value;

    displaySubjects();

    checklist.innerHTML = "<li>Select your subjects first.</li>";

});


/* ADD SUBJECT */

addSubject.addEventListener("click", function () {

    const subjectName = subject.value.trim();

    if (subjectName === "") {

        alert("Please enter a subject.");

        return;

    }

    schedules[day.value].push(subjectName);

    subject.value = "";

    displaySubjects();

});


/* GENERATE CHECKLIST */

generate.addEventListener("click", function () {

    checklist.innerHTML = "";

    let thingsToBring = [
        "📓 Notebook",
        "🖊️ Pen",
        "🪪 Student ID"
    ];


    const selectedType = document.querySelector(
        'input[name="scheduleType"]:checked'
    ).value;


    let todaySubjects = [];


    /* PER DAY */

    if (selectedType === "day") {

        todaySubjects = schedules[day.value];

    }


    /* WHOLE WEEK */

    if (selectedType === "week") {

        const today = new Date();

        const dayNumber = today.getDay();

        const dayNames = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday"
        ];

        const todayName = dayNames[dayNumber];


        if (schedules[todayName] !== undefined) {

            todaySubjects = schedules[todayName];

        }

    }


    todaySubjects.forEach(function (subjectName) {

        const name = subjectName.toLowerCase();


        if (
            name.includes("programming") ||
            name.includes("coding") ||
            name.includes("computer")
        ) {

            thingsToBring.push("💻 Laptop");
            thingsToBring.push("🔌 USB");

        }


        if (name.includes("networking")) {

            thingsToBring.push("🌐 Networking materials");
            thingsToBring.push("💻 Laptop");

        }


        if (
            name === "pe" ||
            name.includes("physical education")
        ) {

            thingsToBring.push("👟 PE Uniform");

        }

    });


    thingsToBring = [...new Set(thingsToBring)];


    thingsToBring.forEach(function (item) {

        const li = document.createElement("li");

        const checkbox = document.createElement("input");

        checkbox.type = "checkbox";


        const label = document.createElement("label");

        label.textContent = item;


        li.appendChild(checkbox);

        li.appendChild(label);

        checklist.appendChild(li);

    });

});

/* SAVE SCHEDULE */

const saveSchedule = document.getElementById("saveSchedule");

saveSchedule.addEventListener("click", function () {

    const selectedType = document.querySelector(
        'input[name="scheduleType"]:checked'
    ).value;


    /* WHOLE WEEK */

    if (selectedType === "week") {

        const monday = document.getElementById("mondaySubject").value.trim();
        const tuesday = document.getElementById("tuesdaySubject").value.trim();
        const wednesday = document.getElementById("wednesdaySubject").value.trim();
        const thursday = document.getElementById("thursdaySubject").value.trim();
        const friday = document.getElementById("fridaySubject").value.trim();


        schedules.Monday = monday === "" ? [] : [monday];
        schedules.Tuesday = tuesday === "" ? [] : [tuesday];
        schedules.Wednesday = wednesday === "" ? [] : [wednesday];
        schedules.Thursday = thursday === "" ? [] : [thursday];
        schedules.Friday = friday === "" ? [] : [friday];

    }


    /* SAVE TO SUPABASE */

    fetch("/save-schedule", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(schedules)

    })

    .then(response => response.json())

    .then(data => {

        alert(
            data.message + "\n\n" + (data.error || "")
        );

    })

    .catch(error => {

        console.error("Error:", error);

        alert("Error: " + error.message);

    });

});


/* CLEAR SCHEDULE */

const clearSchedule = document.getElementById("clearSchedule");

clearSchedule.addEventListener("click", function () {

    const currentDay = day.value;


    const confirmClear = confirm(
        "Are you sure you want to clear " +
        currentDay +
        "'s schedule?"
    );


    if (!confirmClear) {

        return;

    }


    schedules[currentDay] = [];


    displaySubjects();


    checklist.innerHTML =
        "<li>Select your subjects first.</li>";


    fetch("/clear-schedule", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            day: currentDay
        })

    })

    .then(response => response.json())

    .then(data => {

        alert(data.message);

    })

    .catch(error => {

        console.error("Error:", error);

        alert("Failed to clear schedule.");

    });

});


/* LOAD SCHEDULE FROM SUPABASE */

window.addEventListener("load", function () {

    fetch("/load-schedule")

        .then(response => response.json())

        .then(data => {

            data.forEach(function (schedule) {

                if (
                    schedules[schedule.day] !== undefined
                ) {

                    schedules[schedule.day] =
                        schedule.subjects;

                }

            });


            selectedDay.textContent = day.value;

            displaySubjects();

        })

        .catch(error => {

            console.error(
                "Error loading schedule:",
                error
            );

        });

});