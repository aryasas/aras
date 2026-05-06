/* Aras Social — shared helpers */

function getCsrf() {
  var el = document.querySelector('meta[name="csrf-token"]');
  return el ? el.getAttribute('content') : '';
}

function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ── Like ── */
function toggleLike(postId, btn) {
  fetch('/soc/api/posts/' + postId + '/like', {
    method: 'POST', headers: {'X-CSRFToken': getCsrf()}
  }).then(r => r.json()).then(d => {
    if (!d.ok) return;
    btn.classList.toggle('liked', d.data.liked);
    var stats = btn.closest('[data-post-id]').querySelector('.soc-post-stats span');
    if (stats) {
      var count = parseInt(stats.textContent) || 0;
      var newCount = d.data.liked ? count + 1 : Math.max(0, count - 1);
      stats.innerHTML = newCount
        ? '<i class="fa fa-thumbs-up" style="color:var(--fb-blue);"></i> ' + newCount
        : '';
    }
  });
}

/* ── Comments ── */
function showComments(postId) {
  var section = document.getElementById('comments-' + postId);
  if (!section) return;
  var visible = section.style.display !== 'none';
  section.style.display = visible ? 'none' : 'block';
  if (!visible) loadComments(postId);
}

function loadComments(postId) {
  fetch('/soc/api/posts/' + postId + '/comments')
    .then(r => r.json()).then(d => {
      var list = document.querySelector('#comments-' + postId + ' .comment-list');
      if (!list) return;
      if (!d.data || !d.data.length) {
        list.innerHTML = '<p style="font-size:13px;color:var(--fb-muted);margin:0 0 8px;">No comments yet.</p>';
        return;
      }
      list.innerHTML = d.data.map(function(c) {
        return '<div class="soc-comment">' +
          '<div class="soc-avatar sm">' + escHtml(c.author_username[0].toUpperCase()) + '</div>' +
          '<div class="soc-comment-bubble">' +
          '<strong>' + escHtml(c.author_username) + '</strong>' +
          '<p>' + escHtml(c.content) + '</p>' +
          '</div></div>';
      }).join('');
    });
}

function submitComment(postId) {
  var input = document.querySelector('.comment-input[data-post="' + postId + '"]');
  if (!input || !input.value.trim()) return;
  fetch('/soc/api/comments', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrf()},
    body: JSON.stringify({post_id: postId, content: input.value.trim()})
  }).then(r => r.json()).then(d => {
    if (d.ok) { input.value = ''; loadComments(postId); }
  });
}

/* ── Share ── */
function sharePost(postId) {
  var content = prompt('Add a message (optional):') || '';
  fetch('/soc/api/posts/' + postId + '/share', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrf()},
    body: JSON.stringify({content: content, visibility: 'friends'})
  }).then(r => r.json()).then(d => { if (d.ok) location.reload(); });
}

/* ── Delete post ── */
async function deletePost(postId) {
  if (!await confirm('Delete this post?')) return;
  fetch('/soc/api/posts/' + postId, {
    method: 'DELETE', headers: {'X-CSRFToken': getCsrf()}
  }).then(r => r.json()).then(d => {
    if (d.ok) {
      var card = document.querySelector('[data-post-id="' + postId + '"]');
      if (card) { card.style.opacity = '0'; setTimeout(function() { card.remove(); }, 300); }
    }
  });
}
