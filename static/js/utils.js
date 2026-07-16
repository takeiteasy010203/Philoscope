document.getElementById('myForm').addEventListener('submit', async function(e) {
    e.preventDefault(); 
    
    const btn = document.getElementById('submitBtn');
    const text = document.getElementById('btnText');
    const spinner = document.getElementById('btnSpinner');
    const responseArea = document.getElementById('responseArea');
    const question = document.getElementById('questionInput').value
    
    btn.disabled = true;
    text.textContent = 'Loading...';
    spinner.classList.remove('d-none');
    


    const formData = new FormData(this);
    
try {
        const response = await fetch('/', {
            method: 'POST',
            body: formData
        });

const result = await response.json();
        
if (!response.ok) {
    throw new Error(result.detail);
}


// ✅ Lấy dữ liệu từ result
const question_id = result.question_id || '';
const json_qdata = result.json_qdata || {};


        // In response ra màn hình
responseArea.innerHTML = `
            <div class="px-2 border border-3 border-primary rounded"> 
        <div class="text-center">
            <span class="display-5  fst-italic  fw-semibold" >ANALYSIS📜</span>
        </div>

        <div class="plot-container">
            
            <div id="content_block" class="d-flex align-items-start flex-column summary-box plot-wrapper">
                 
               
            </div>
            <div id="chart-box" class="chart-box  justify-content-center align-items-center my-3">
                
            </div>
            <div class="download_container d-flex flex-column">
                <div class="">
                    📄 Report Ready
                    <br>
                    Your personalized report has been generated.
                </div>
                <a
                    href="/download/${question_id}"
                    target="_blank"
                    class="btn btn-outline-primary my-2"
                >
                        📄 Download Report
                </a>
            </div>  
            
        </div>

    </div>
        `;
const content_block = document.getElementById('content_block')
    
    Object.entries(json_qdata).forEach(
        ([mainKey, mainValue]) => {
    const label = document.createElement('div')
    label.classList.add('text_label')
    label.textContent = mainValue['label']
    const evidence = document.createElement('div')
    evidence.classList.add('text_evidence')
    evidence.textContent = mainValue['evidence'] || ''
    content_block.append(label)
    content_block.append(evidence)
    }
)
const graphData = JSON.parse(result.graph_data);

const graphLayout = JSON.parse(result.graph_layout);

Plotly.newPlot(
    'chart-box',
    graphData,
    graphLayout,
    {
        responsive: true
    }
)
        
    } catch (error) {
        responseArea.innerHTML = `
            <div class="alert alert-danger">
                Error: ${error.message}
            </div>
        `;
        console.error('Error:', error);
    } finally {
    
        btn.disabled = false;
        text.textContent = '😎 Generate Report';
        spinner.classList.add('d-none');
    }
});
