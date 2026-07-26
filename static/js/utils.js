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
            <div class="px-2 "> 
        <div class="plot-container">
            <div id="content_block" class="d-flex align-items-start flex-column summary-box plot-wrapper">
                <div class="text_block_1 shadow-hover shadow p-3 row rounded-3 mb-3 ">
                    <img src="/media/Team work-rafiki.svg" class="col-md-4 text_pic" alt="">
                    <div class="inside_content col-md-8">
                        <div class="text_label_1 text_label align-items-center lh-lg"></div>
                        <div class="text_evidence_1 text_evidence "></div>
                    </div>
                </div>

                <div class="text_block_2 shadow-hover shadow p-3 row rounded-3 mb-3 ">
                    <img src="/media/Design thinking-rafiki.svg" class="col-md-4 text_pic" alt="">
                    <div class="inside_content col-md-8">
                        <div class="text_label_2 text_label align-items-center lh-lg"></div>
                        <div class="text_evidence_2 text_evidence "></div>
                    </div>
                </div>

                <div class="text_block_3 shadow-hover shadow p-3 row rounded-3 mb-3 ">
                    <img src="/media/Solar system-rafiki.svg" class="col-md-4 text_pic" alt="">
                    <div class="inside_content col-md-8">
                        <div class="text_label_3 text_label align-items-center lh-lg"></div>
                        <div class="text_evidence_3 text_evidence "></div>
                    </div>
                </div>

                <div class="text_block_4 shadow-hover shadow p-3 row rounded-3 mb-3 ">
                    <img src="/media/Choose-rafiki.svg" class="col-md-4 text_pic" alt="">
                    <div class="inside_content col-md-8">
                        <div class="text_label_4 text_label align-items-center lh-lg"></div>
                        <div class="text_evidence_4 text_evidence "></div>
                    </div>
                </div>
               
               
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
//1
const text_label_1 = content_block.querySelector('.text_label_1');
const text_evidence_1 = content_block.querySelector('.text_evidence_1');
//2
const text_label_2 = content_block.querySelector('.text_label_2');
const text_evidence_2 = content_block.querySelector('.text_evidence_2');
//3
const text_label_3 = content_block.querySelector('.text_label_3');
const text_evidence_3 = content_block.querySelector('.text_evidence_3');
//4
const text_label_4 = content_block.querySelector('.text_label_4');
const text_evidence_4 = content_block.querySelector('.text_evidence_4');
    Object.entries(json_qdata).forEach(
        ([mainKey, mainValue]) => {
            text_label_1.textContent = json_qdata["individualism_collectivism"].label;
            text_evidence_1.textContent = json_qdata["individualism_collectivism"].evidence;
           
            text_label_2.textContent = json_qdata["rationalism_irrationalism"].label;
            text_evidence_2.textContent = json_qdata["rationalism_irrationalism"].evidence;
           
            text_label_3.textContent = json_qdata["universalism_relativism"].label;
            text_evidence_3.textContent = json_qdata["universalism_relativism"].evidence;
           
            text_label_4.textContent = json_qdata["determinism_free_will"].label;
            text_evidence_4.textContent = json_qdata["determinism_free_will"].evidence;
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
