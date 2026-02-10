alert("Working test");

document.addEventListener("DOMContentLoaded", function () {

    // --- 1. THE CALCULATION ENGINE ---
    function calculateTotals() {
        let grandTotal = 0;
        let totalTax = 0;

        const rows = document.querySelectorAll(".purchaseMedicineRow");

        rows.forEach(row => {
            // Targeting your specific class names
            const qtyInput = row.querySelector(".purchaseMedicine_Qty");
            const priceInput = row.querySelector(".purchaseMedicine_Price");
            const taxInput = row.querySelector(".purchaseMedicineTax_Row");
            const rowAmountInput = row.querySelector(".purchaseMedicine_Amount");

            const qty = parseFloat(qtyInput?.value) || 0;
            const price = parseFloat(priceInput?.value) || 0;
            const tax = parseFloat(taxInput?.value) || 0;

            // Row calculation: (Quantity * Price) + Tax
            const rowTotal = (qty * price) + tax;
            
            if (rowAmountInput) {
                rowAmountInput.value = rowTotal.toFixed(2);
            }

            grandTotal += rowTotal;
            totalTax += tax;
        });

        // Update Bottom Summary fields using IDs
        const totalField = document.getElementById("purchaseMedicineTotalAmount");
        const taxField = document.getElementById("purchaseMedicineTax");
        const discPercInput = document.getElementById("purchaseMedicineDiscPerc");
        const discAmtField = document.getElementById("purchaseMedicineDiscount");
        const netField = document.getElementById("purchaseMedicineNetAmount");
        const payField = document.getElementById("paymentMedicinePayAmount");

        const discPerc = parseFloat(discPercInput?.value) || 0;
        const discAmount = (grandTotal * discPerc) / 100;
        const netAmount = grandTotal - discAmount;

        if (totalField) totalField.value = grandTotal.toFixed(2);
        if (taxField) taxField.value = totalTax.toFixed(2);
        if (discAmtField) discAmtField.value = discAmount.toFixed(2);
        if (netField) netField.value = netAmount.toFixed(2);
        if (payField) payField.value = netAmount.toFixed(2);
    }

    // --- 2. ATTACH EVENTS TO A ROW ---
    function initRow(row) {
        // Recalculate whenever any input in the row changes
        row.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', calculateTotals);
        });

        // Handle Category -> Medicine dropdown fetch
        const catSelect = row.querySelector(".purchaseMedicine_Category");
        const medSelect = row.querySelector(".purchaseMedicine_Name");

        if (catSelect && medSelect) {
            catSelect.addEventListener("change", function () {
                const catId = this.value;
                medSelect.innerHTML = '<option value="">---Select---</option>';
                if (!catId) return;

                fetch(`/pharmacy/get-medicines-by-category/${catId}/`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === "success") {
                            data.medicines.forEach(m => {
                                const opt = document.createElement("option");
                                opt.value = m.id;
                                opt.textContent = m.name;
                                medSelect.appendChild(opt);
                            });
                        }
                    });
            });
        }
    }

    // --- 3. ROW CLONING ---
    const addBtn = document.querySelector(".purchaseMediceAddRowBtn");
    const container = document.getElementById("purchaseMedicineRowsContainer");

    if (addBtn && container) {
        addBtn.addEventListener("click", function () {
            const original = document.querySelector(".purchaseMedicineRow");
            const clone = original.cloneNode(true);

            // Clean values and remove IDs to keep the browser happy
            clone.querySelectorAll("input, select").forEach(i => {
                i.value = "";
                i.removeAttribute("id"); 
            });

            // Clean out labels for the cloned row
            clone.querySelectorAll("label").forEach(l => l.remove());

            // Setup the Delete Button using your preferred CSS class
            const actionBtn = clone.querySelector(".purchaseMediceAddRowBtn");
            if (actionBtn) {
                actionBtn.innerHTML = "×";
                // Replace "Add" class with your "Delete" class
                actionBtn.classList.replace("purchaseMediceAddRowBtn", "purchaseMedicineDeleteRowBtn");
                
                // Ensure no leftover inline styles from the + button interfere
                actionBtn.removeAttribute('style'); 

                actionBtn.onclick = () => { 
                    clone.remove(); 
                    calculateTotals(); 
                };
            }

            // Insert new row before the HR
            container.insertBefore(clone, container.querySelector("hr"));
            initRow(clone);
        });
    }

    // --- 4. INITIALIZE ---
    // Set default date to today in YYYY-MM-DD format
    const dateInput = document.getElementById("purchaseMedicineDateInput");
    console.log("Date input found:", dateInput); // DEBUG
    
    if (dateInput) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}`;
        
        dateInput.value = formattedDate;
        console.log("Date set to:", formattedDate); // DEBUG
        console.log("Date input value after setting:", dateInput.value); // DEBUG
    } else {
        console.error("Date input NOT found!"); // DEBUG
    }

    const firstRow = document.querySelector(".purchaseMedicineRow");
    if (firstRow) initRow(firstRow);
    
    document.getElementById("purchaseMedicineDiscPerc")?.addEventListener("input", calculateTotals);

    // Auto-generate bill number on page load
    generateBillNumber();
    
    function generateBillNumber() {
        const timestamp = Date.now();
        const billNo = 'PUR-' + timestamp;
        const billInput = document.getElementById('purchaseMedicineBillNo');
        if (billInput) {
            billInput.value = billNo;
        }
    }

    // --- 5. SAVE BUTTON ---
    const saveBtn = document.getElementById("purchaseMedicineSaveBtn");
    if (saveBtn) {
        saveBtn.addEventListener("click", function (e) {
            e.preventDefault();
            savePurchase();
        });
    }
    
    function savePurchase() {
        console.log("=== SAVE PURCHASE CALLED ==="); // DEBUG
        
        // Get supplier
        const supplierId = document.getElementById('supplierName').value;
        console.log("Supplier ID:", supplierId); // DEBUG
        
        if (!supplierId) {
            alert('Please select a supplier');
            return;
        }
        
        // Get bill details
        const billNo = document.getElementById('purchaseMedicineBillNo').value;
        console.log("Bill No:", billNo); // DEBUG
        
        const purchaseDateInput = document.getElementById('purchaseMedicineDateInput');
        console.log("Purchase date input element:", purchaseDateInput); // DEBUG
        
        const purchaseDate = purchaseDateInput ? purchaseDateInput.value : '';
        console.log("Purchase date value:", purchaseDate); // DEBUG
        console.log("Purchase date length:", purchaseDate.length); // DEBUG
        console.log("Purchase date type:", typeof purchaseDate); // DEBUG
        
        // Validate date format
        if (!purchaseDate || purchaseDate.trim() === '') {
            alert('Purchase date is required. Please refresh the page.');
            console.error("Purchase date is empty!"); // DEBUG
            return;
        }
        
        const note = document.getElementById('purchaseMedicineNote').value;
        
        // Collect all medicine rows
        const medicineRows = document.querySelectorAll('.purchaseMedicineRow');
        const medicines = [];
        
        medicineRows.forEach(row => {
            const drugSelect = row.querySelector('.purchaseMedicine_Name');
            const batchNo = row.querySelector('.purchaseMedicineBatch_No')?.value;
            const expiryDate = row.querySelector('.purchaseMedicineExpiry_Date')?.value;
            const quantity = row.querySelector('.purchaseMedicine_Qty')?.value;
            const purchasePrice = row.querySelector('.purchaseMedicine_Price')?.value;
            const salePrice = row.querySelector('.purchaseMedicineSale_Price')?.value;
            
            if (drugSelect && drugSelect.value && quantity && purchasePrice) {
                medicines.push({
                    drug_id: drugSelect.value,
                    batch_no: batchNo,
                    expiry_date: expiryDate,
                    quantity: quantity,
                    purchase_price: purchasePrice,
                    sale_price: salePrice
                });
            }
        });
        
        console.log("Medicines collected:", medicines.length); // DEBUG
        
        if (medicines.length === 0) {
            alert('Please add at least one medicine');
            return;
        }
        
        // Prepare data
        const purchaseData = {
            supplier_id: supplierId,
            bill_no: billNo,
            purchase_date: purchaseDate,
            note: note,
            medicines: medicines
        };
        
        console.log("Final purchase data:", JSON.stringify(purchaseData, null, 2)); // DEBUG
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Send to server
        fetch('/pharmacy/save-medicine-purchase/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(purchaseData)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data); // DEBUG
            if (data.status === 'success') {
                alert(data.message);
                window.location.href = '/pharmacy/pharmacy/medicinepurchaselist/'; // Redirect to list page
                
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while saving the purchase');
        });
    }

    // Calculate totals when quantity or price changes
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('purchaseMedicine_Qty') || 
            e.target.classList.contains('purchaseMedicine_Price') ||
            e.target.classList.contains('purchaseMedicineTax_Row')) {
            calculateRowAmount(e.target.closest('.purchaseMedicineRow'));
            calculateTotals();
        }
        
        if (e.target.id === 'purchaseMedicineDiscPerc') {
            calculateTotals();
        }
    });
    
    function calculateRowAmount(row) {
        const qty = parseFloat(row.querySelector('.purchaseMedicine_Qty')?.value) || 0;
        const price = parseFloat(row.querySelector('.purchaseMedicine_Price')?.value) || 0;
        const tax = parseFloat(row.querySelector('.purchaseMedicineTax_Row')?.value) || 0;
        
        const amount = (qty * price) + tax;
        const amountField = row.querySelector('.purchaseMedicine_Amount');
        if (amountField) {
            amountField.value = amount.toFixed(2);
        }
    }
    
});