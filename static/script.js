const getCookie =  (name) => {
    let cookieArr = document.cookie.split(";");
    for (let i = 0; i < cookieArr.length; i++) {
        let cookiePair = cookieArr[i].split("=");
        if (name == cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}

const createNotification = (message, type, timeout) => {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="close-btn">&times;</button>
    `;
    document.getElementById('notifications').appendChild(notification);

    notification.querySelector('.close-btn').addEventListener('click', function() {
        fadeOutAndRemove(notification);
    });

    setTimeout(() => {
        fadeOutAndRemove(notification);
    }, timeout*1000);
}

const fadeOutAndRemove = (element) => {
    element.classList.add('fade-out');
    element.addEventListener('transitionend', () => {
        element.remove();
    });
}

const socket = io({
    autoConnect: false
});

document.addEventListener('DOMContentLoaded', function() {
    socket.connect();
    
    var form = document.getElementById('pushCourseForm');
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        var formData = new FormData(form);
        var code = formData.get('code');
        var notionID = getCookie('notionID');
        socket.emit("pushCourseForm", {
            code: code,
            notionID: notionID
        });
        createNotification(`Pushing COMP${code} to Notion`, "info", 10);

        fetch('/pushcourse', {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                console.log('Form submitted successfully');
            } else {
                console.error('Form submission failed');
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    });

    socket.on('status_update', function(data) {
        createNotification(data.message, data.type, 3);
    });

    socket.on('status_update_IMP', function(data) {
        createNotification(data.message, data.type, 7);
    });

    socket.on('injectsModulePageNotionID', function(data) {
        const { modulePageId, code } = data;
        const form = document.querySelector(`form[data-code="${code}"]`);
        if (form) {
            const parentTd = form.parentElement;
            parentTd.innerHTML = `<a href="https://www.notion.so/${modulePageId}" target="_blank">notion.so</a>`;
        } else {
            const tableBody = document.querySelector('table.table tbody');
            if (tableBody) {
                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td>${code}</td>
                    <td><a href="https://www.notion.so/${modulePageId}" target="_blank">notion.so</a></td>
                `;
                tableBody.appendChild(newRow);
            }
        }
    });
})