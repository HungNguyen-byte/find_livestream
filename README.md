<h1>Youtube Livestream</h1>
<p>Thư viện cần cài đặt:</p>
<p><strong>pip install requests google-api-python-client google-auth-oauthlib pandas openpyxl python-dotenv</strong></p>
<p>Bước của các file</p>
<ol>
  <li><strong>"youtube_token":</strong> tạo file "token.pickle"</li>
  <li><strong>"youtube_agent":</strong> thực hiện việc tìm kiếm thông tin livestream trên youtube + tự động nhắn vào stream</li>
  <li><strong>"youtube_token":</strong> lọc dữ liệu và tọa ra file excel</li>
</ol>

<p>Khó khăn</p>
<ul>
  <li>Nhắn tin tự động còn hạn chế do nó chưa xác định được thời gian hoặc stram không mở đoạn chat</li>
  <li>Lọc dữ liệu còn hạn chế do chưa có định dạng thời gian tốt</li>
</ul>
