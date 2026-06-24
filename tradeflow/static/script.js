async function uploadFile() {

    const fileInput = document.getElementById("fileInput");
    const loader = document.getElementById("loader");
    const resultDiv = document.getElementById("result");
    const badge = document.getElementById("statusBadge");
    const extractedData = document.getElementById("extractedData");
    const complianceData = document.getElementById("complianceData");

    if (!fileInput.files.length) {
        alert("Please select a file.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    loader.classList.remove("hidden");
    resultDiv.classList.add("hidden");

    const response = await fetch("/upload/", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    loader.classList.add("hidden");
    resultDiv.classList.remove("hidden");

    // Display extracted data
    extractedData.textContent = JSON.stringify(data.extracted_data, null, 2);

    // Display compliance
    complianceData.textContent = JSON.stringify(data.compliance_result, null, 2);

    // Status badge styling
    const status = data.compliance_result.status;

    badge.textContent = "Status: " + status;

    badge.className = "badge";

    if (status === "ALLOWED") {
        badge.classList.add("approved");
    } else if (status === "RESTRICTED") {
        badge.classList.add("restricted");
    } else if (status === "PROHIBITED") {
        badge.classList.add("prohibited");
    } else {
        badge.classList.add("restricted");
    }
}