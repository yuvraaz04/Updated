// Global variables
let cameraActive = false;
let videoStream = null;
let autoCapture = true; // Set to true to enable automatic face capture

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize section-group dynamic selection if on selection page
    const sectionSelect = document.getElementById('section');
    if (sectionSelect) {
        sectionSelect.addEventListener('change', function() {
            updateGroups(this.value);
        });
        
        // Initial load of groups
        if (sectionSelect.value) {
            updateGroups(sectionSelect.value);
        }
    }
    
    // Initialize attendance marking if on attendance page
    setupAttendanceMarking();
});

// Function to update groups based on selected section
function updateGroups(sectionId) {
    if (!sectionId) return;
    
    const groupSelect = document.getElementById('group');
    if (!groupSelect) return;
    
    // Clear current options
    groupSelect.innerHTML = '<option value="">Select Group</option>';
    
    // Fetch groups for the selected section
    fetch(`/get_groups/${sectionId}`)
        .then(response => response.json())
        .then(groups => {
            groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group.id;
                option.textContent = group.name;
                groupSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching groups:', error);
        });
}

// Setup attendance marking functionality
function setupAttendanceMarking() {
    const attendanceCards = document.querySelectorAll('.attendance-card');
    if (!attendanceCards.length) return;
    
    attendanceCards.forEach(card => {
        const presentBtn = card.querySelector('.btn-present');
        const absentBtn = card.querySelector('.btn-absent');
        const studentId = card.dataset.studentId;
        
        if (presentBtn) {
            presentBtn.addEventListener('click', function() {
                startCamera(studentId);
            });
        }
        
        if (absentBtn) {
            absentBtn.addEventListener('click', function() {
                markAttendance(studentId, 'absent');
            });
        }
    });
    
    // Setup camera capture button
    const captureBtn = document.getElementById('capture-photo');
    if (captureBtn) {
        captureBtn.addEventListener('click', capturePhoto);
    }
    
    // Setup camera cancel button
    const cancelBtn = document.getElementById('cancel-camera');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeCamera);
    }
    
    // Show notification about auto face capture
    const cameraModal = document.getElementById('camera-modal');
    if (cameraModal) {
        cameraModal.addEventListener('shown.bs.modal', function() {
            if (autoCapture) {
                // Show notification to student
                const modalBody = cameraModal.querySelector('.modal-body');
                const notification = document.createElement('div');
                notification.className = 'alert alert-info mt-3';
                notification.innerHTML = `<i class="fas fa-info-circle"></i> Looking for your face. Please look at the camera.`;
                modalBody.appendChild(notification);
                
                // Schedule automatic capture after 2 seconds
                setTimeout(() => {
                    if (cameraActive) {
                        capturePhoto();
                    }
                }, 2000);
            }
        });
    }
}

// Function to start the camera
function startCamera(studentId) {
    const cameraModal = document.getElementById('camera-modal');
    const videoElement = document.getElementById('camera-feed');
    const currentStudentIdInput = document.getElementById('current-student-id');
    
    if (!cameraModal || !videoElement || !currentStudentIdInput) return;
    
    // Set the current student ID
    currentStudentIdInput.value = studentId;
    
    // Show the modal
    const modal = new bootstrap.Modal(cameraModal);
    modal.show();
    
    // Access the webcam
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            videoStream = stream;
            videoElement.srcObject = stream;
            videoElement.play();
            cameraActive = true;
        })
        .catch(error => {
            console.error('Error accessing webcam:', error);
            alert('Error accessing webcam. Please make sure your camera is connected and permissions are granted.');
            modal.hide();
        });
}

// Function to capture photo
function capturePhoto() {
    if (!cameraActive) return;
    
    const videoElement = document.getElementById('camera-feed');
    const currentStudentIdInput = document.getElementById('current-student-id');
    const spinnerElement = document.getElementById('camera-spinner');
    
    if (!videoElement || !currentStudentIdInput) return;
    
    const studentId = currentStudentIdInput.value;
    
    // Show spinner
    if (spinnerElement) spinnerElement.classList.remove('hidden');
    
    // Create a canvas element to capture the frame
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    
    // Get the image data as base64
    const imageData = canvas.toDataURL('image/jpeg');
    
    // Mark the attendance with the captured image
    markAttendance(studentId, 'present', imageData);
}

// Function to close the camera
function closeCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    
    const cameraModal = document.getElementById('camera-modal');
    if (cameraModal) {
        const modal = bootstrap.Modal.getInstance(cameraModal);
        if (modal) modal.hide();
    }
    
    cameraActive = false;
}

// Function to mark attendance
function markAttendance(studentId, status, imageData = null) {
    // Create data object
    const data = {
        student_id: studentId,
        status: status
    };
    
    // Add image data if present
    if (status === 'present' && imageData) {
        data.image_data = imageData;
    }
    
    // Show loading state
    const studentCard = document.querySelector(`.attendance-card[data-student-id="${studentId}"]`);
    if (studentCard) {
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        spinner.id = `spinner-${studentId}`;
        studentCard.appendChild(spinner);
        
        // Disable buttons
        const buttons = studentCard.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = true);
    }
    
    // Send data to server
    fetch('/process_attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        // Close camera if open
        closeCamera();
        
        if (result.success) {
            // Update UI to show attendance status
            updateAttendanceUI(studentId, status);
            
            // Check if all students have attendance marked
            checkAllAttendanceMarked();
        } else {
            alert(`Error: ${result.message}`);
            
            // Re-enable buttons if error
            if (studentCard) {
                const buttons = studentCard.querySelectorAll('button');
                buttons.forEach(btn => btn.disabled = false);
            }
        }
        
        // Remove spinner
        const spinner = document.getElementById(`spinner-${studentId}`);
        if (spinner) spinner.remove();
    })
    .catch(error => {
        console.error('Error marking attendance:', error);
        alert('Error marking attendance. Please try again.');
        
        // Close camera if open
        closeCamera();
        
        // Remove spinner
        const spinner = document.getElementById(`spinner-${studentId}`);
        if (spinner) spinner.remove();
        
        // Re-enable buttons
        if (studentCard) {
            const buttons = studentCard.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = false);
        }
    });
}

// Function to update UI after attendance is marked
function updateAttendanceUI(studentId, status) {
    const studentCard = document.querySelector(`.attendance-card[data-student-id="${studentId}"]`);
    if (!studentCard) return;
    
    // Set background color based on status
    if (status === 'present') {
        studentCard.style.borderLeft = '5px solid #04AA6D';
    } else {
        studentCard.style.borderLeft = '5px solid #d9534f';
    }
    
    // Update status text
    const statusElement = studentCard.querySelector('.attendance-status');
    if (statusElement) {
        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        statusElement.style.color = status === 'present' ? '#04AA6D' : '#d9534f';
    }
    
    // Disable buttons
    const buttons = studentCard.querySelectorAll('button');
    buttons.forEach(btn => btn.disabled = true);
    
    // Add marked flag
    studentCard.dataset.marked = 'true';
}

// Check if all students have attendance marked
function checkAllAttendanceMarked() {
    const cards = document.querySelectorAll('.attendance-card');
    const allMarked = Array.from(cards).every(card => card.dataset.marked === 'true');
    
    if (allMarked) {
        // Show summary button if all marked
        const summaryBtn = document.getElementById('view-summary-btn');
        if (summaryBtn) {
            summaryBtn.style.display = 'inline-block';
        }
    }
}