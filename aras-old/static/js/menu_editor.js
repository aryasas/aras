var ME = (function(){
  var _data = null;       // [{id, name, title, icon, in_sidebar, menu_order, tables:[...nested...]}]
  var _drag = null;       // {nodeId, appId, type:'app'|'table'}
  var _editId = null;
  var _editType = null;

  /* ── helpers ─────────────────────────────────────────────────────────── */
  function esc(s){ var d=document.createElement('div'); d.textContent=s||''; return d.innerHTML; }
  function iconCls(ic){ if(!ic) return 'fa fa-circle'; return ic.startsWith('ti-') ? ic : 'fa '+ic; }
  function iconEl(ic){ return '<i class="'+iconCls(ic)+' me-icon"></i>'; }

  function flatten(nodes, out){
    out = out||[];
    (nodes||[]).forEach(function(n){ out.push(n); flatten(n.children,out); });
    return out;
  }
  function findNode(nodes, id){
    for(var i=0;i<nodes.length;i++){
      if(nodes[i].id===id) return nodes[i];
      var r=findNode(nodes[i].children,id);
      if(r) return r;
    }
    return null;
  }
  function removeNode(nodes, id){
    for(var i=0;i<nodes.length;i++){
      if(nodes[i].id===id){ return nodes.splice(i,1)[0]; }
      var r=removeNode(nodes[i].children,id);
      if(r) return r;
    }
    return null;
  }
  function findParentList(nodes, id){
    for(var i=0;i<nodes.length;i++){
      if(nodes[i].id===id) return nodes;
      var r=findParentList(nodes[i].children,id);
      if(r) return r;
    }
    return null;
  }
  function reindex(nodes, parentId){
    (nodes||[]).forEach(function(n,i){
      n.menu_order=i; n.parent_table_id=parentId||null;
      reindex(n.children, n.id);
    });
  }
  function appOf(tableId){
    for(var i=0;i<_data.length;i++){
      if(findNode(_data[i].tables, tableId)) return _data[i];
    }
    return null;
  }

  /* ── render ───────────────────────────────────────────────────────────── */
  function renderNode(node, appId){
    var isGroup  = node.is_group || !node.db_backed;
    var hidden   = !node.show_in_menu;
    var hasKids  = node.children && node.children.length > 0;
    var kidId    = 'kids_' + node.id + '_' + appId;

    var kidsHtml = '';
    if(hasKids){
      var inner = node.children.map(function(c){ return renderNode(c, appId); }).join('');
      kidsHtml = '<div class="me-nest" id="'+kidId+'">' + inner + '</div>';
    }

    if(isGroup){
      var togBtn = hasKids ? '<span class="me-grp-tog" id="tog_'+kidId+'" onclick="ME.toggleKids(event,\''+kidId+'\')"><i class="ti-angle-right"></i></span>' : '';
      var isCustomGrp = node.db_backed && node.id > 0;
      return (
        '<div class="me-group-block" data-nid="'+node.id+'" data-app="'+appId+'">' +
          '<div class="me-group-hdr" style="cursor:pointer;" onclick="ME.rowClick(event,\'table\','+node.id+')">' +
            togBtn + iconEl(node.icon) + '<span class="me-group-label">'+esc(node.title)+'</span>' +
            '<span class="me-group-pill">group</span><span class="me-row-actions">' +
              (isCustomGrp ? '<button class="me-del-btn" title="Delete group" onclick="ME.deleteItem(event,'+node.id+')"><i class="ti-trash"></i></button>' : '') +
            '</span>' +
          '</div>' + kidsHtml +
        '</div>'
      );
    }

    var isCustom = node.is_group || (node.name && (node.name+'').startsWith('_grp_')) || (node.name && (node.name+'').startsWith('_page_'));
    return (
      '<div class="me-item-wrap" data-nid="'+node.id+'" data-app="'+appId+'">' +
        '<div class="me-row'+(hidden?' me-opacity-50':'')+'" data-row="'+node.id+'" draggable="true" ' +
             'onclick="ME.rowClick(event,\'table\','+node.id+')" ' +
             'ondragstart="ME.dragStart(event,\'table\','+node.id+','+appId+')" ' +
             'ondragend="ME.dragEnd(event)" ondragover="ME.dragOverRow(event,\''+node.id+'\')" ' +
             'ondragleave="ME.dragLeaveRow(event)" ondrop="ME.dropRow(event,\'table\',\''+node.id+'\',\''+appId+'\')">' +
          '<span class="me-handle" onclick="event.stopPropagation()"><i class="ti-menu-alt"></i></span>' +
          (hasKids ? '<span class="me-toggle open" id="tog_'+kidId+'" onclick="ME.toggleKids(event,\''+kidId+'\')"><i class="ti-angle-right"></i></span>' : '<span style="width:16px;flex-shrink:0"></span>') +
          iconEl(node.icon) + '<span class="me-label">'+esc(node.title)+'</span>' +
          (hidden ? '<span class="aras-badge bg-light-aras text-muted-aras fs-10 ml-2">hidden</span>' : '') +
          '<span class="me-row-actions">' +
            (isCustom ? '<button class="me-del-btn" title="Delete" onclick="ME.deleteItem(event,'+node.id+')"><i class="ti-trash"></i></button>' : '') +
          '</span>' +
        '</div>' + kidsHtml +
      '</div>'
    );
  }

  function renderApp(app){
    var hasKids  = app.tables && app.tables.length > 0;
    var nodesHtml = (app.tables||[]).map(function(t){ return renderNode(t, app.id); }).join('');
    var isDbApp  = app.db_backed !== false;
    return (
      '<div class="me-app" data-app-id="'+app.id+'">' +
        '<div class="me-app-header" ' + (isDbApp ? 'draggable="true" ' : '') + 'onclick="'+(isDbApp ? 'ME.rowClick(event,\'app\','+app.id+')' : 'ME.toggleApp(event,'+app.id+')')+'" ' +
             (isDbApp ? 'ondragstart="ME.dragStart(event,\'app\','+app.id+',null)" ondragend="ME.dragEnd(event)" ondragover="ME.dragOverApp(event,'+app.id+')" ondragleave="ME.dragLeaveApp(event)" ondrop="ME.dropApp(event,'+app.id+')"' : '') + '>' +
          (isDbApp ? '<i class="ti-menu-alt me-handle" onclick="event.stopPropagation()" style="font-size:12px;color:#8a9bb0"></i>' : '') +
          iconEl(app.icon) + '<span style="flex:1;font-size:13px;font-weight:700;font-family:var(--aras-font-serif);font-style:italic;">'+esc(app.title)+'</span>' +
          (!app.in_sidebar ? '<span class="aras-badge bg-light-aras text-muted-aras fs-10 mr-2">hidden</span>' : '') +
          (hasKids ? '<i class="ti-angle-right me-app-chevron open" id="appchev_'+app.id+'"></i>' : '') +
        '</div>' +
        '<div class="me-app-body" id="appbody_'+app.id+'">' + nodesHtml + '</div>' +
      '</div>'
    );
  }

  function render(){
    if(!_data) return;
    document.getElementById('menuEditorRoot').innerHTML = (_data||[]).map(renderApp).join('');
  }

  function toggleKids(e, kidId){
    e.stopPropagation();
    var kids = document.getElementById(kidId);
    var tog  = document.getElementById('tog_'+kidId);
    if(!kids) return;
    var hidden = kids.style.display==='none';
    kids.style.display = hidden ? '' : 'none';
    if(tog){ tog.classList.toggle('open', hidden); }
  }

  function toggleApp(e, appId){
    e.stopPropagation();
    var body = document.getElementById('appbody_'+appId);
    var chev = document.getElementById('appchev_'+appId);
    if(!body) return;
    var hidden = body.style.display==='none';
    body.style.display = hidden ? '' : 'none';
    if(chev) chev.classList.toggle('open', hidden);
  }

  function drawerOpen(type, id){
    _editType = type; _editId = id;
    document.getElementById('medit_type').value = type;
    document.getElementById('medit_id').value = id;
    var prow  = document.getElementById('medit_parent_row');
    var srow  = document.getElementById('medit_show_row');
    var sbrow = document.getElementById('medit_sidebar_row');

    if(type==='app'){
      var app = _data.find(function(a){ return a.id===id; });
      document.getElementById('meDrawer_title').textContent = app.title;
      document.getElementById('medit_title').value = app.title;
      document.getElementById('medit_icon').value  = app.icon||'';
      document.getElementById('medit_in_sidebar').checked = app.in_sidebar!==false;
      prow.style.display='none'; srow.style.display='none'; sbrow.style.display='';
    } else {
      var foundApp=null, found=null;
      _data.forEach(function(a){
        var f=findNode(a.tables,id);
        if(f){ found=f; foundApp=a; }
      });
      if(!found) return;
      document.getElementById('meDrawer_title').textContent = found.title;
      document.getElementById('medit_title').value = found.title;
      document.getElementById('medit_icon').value  = found.icon||'';
      document.getElementById('medit_show').checked = found.show_in_menu!==false;
      var excluded = flatten([found]).map(function(n){ return n.id; });
      var sel = document.getElementById('medit_parent');
      sel.innerHTML = '<option value="">— top level —</option>';
      function addOpts(nodes, depth){
        (nodes||[]).forEach(function(n){
          if(excluded.indexOf(n.id)>=0) return;
          var prefix = '    '.repeat(depth);
          var opt=document.createElement('option');
          opt.value=n.id; opt.text=prefix+n.title;
          if(n.id===found.parent_table_id) opt.selected=true;
          sel.appendChild(opt);
          addOpts(n.children, depth+1);
        });
      }
      addOpts(foundApp.tables, 0);
      prow.style.display=''; srow.style.display=''; sbrow.style.display='none';
    }
    _updateIconPreview();
    document.getElementById('medit_icon').oninput = _updateIconPreview;
    document.getElementById('meDrawer').style.display='flex';
    document.getElementById('meOverlay').style.display='';
    document.querySelectorAll('.me-row.me-selected,.me-app-header.me-selected').forEach(function(r){ r.classList.remove('me-selected'); });
    var row = document.querySelector('[data-row="'+id+'"]') || document.querySelector('[data-app-id="'+id+'"] .me-app-header');
    if(row) row.classList.add('me-selected');
  }

  function _updateIconPreview(){
    var ic = document.getElementById('medit_icon').value.trim();
    var iconElem = document.getElementById('medit_icon_preview_icon');
    if(iconElem) {
      iconElem.className = iconCls(ic);
    }
  }

  function drawerClose(){
    document.getElementById('meDrawer').style.display='none';
    document.getElementById('meOverlay').style.display='none';
    document.querySelectorAll('.me-row.me-selected,.me-app-header.me-selected').forEach(function(r){ r.classList.remove('me-selected'); });
  }

  function drawerApply(){
    var type  = document.getElementById('medit_type').value;
    var id    = parseInt(document.getElementById('medit_id').value);
    var title = document.getElementById('medit_title').value.trim();
    var icon  = document.getElementById('medit_icon').value.trim();

    if(type==='app'){
      var app = _data.find(function(a){ return a.id===id; });
      if(app){
        if(title) app.title = title;
        if(icon)  app.icon  = icon;
        app.in_sidebar = document.getElementById('medit_in_sidebar').checked;
      }
    } else {
      var newParent = parseInt(document.getElementById('medit_parent').value)||null;
      var show = document.getElementById('medit_show').checked;
      _data.forEach(function(a){
        var f = findNode(a.tables, id);
        if(!f) return;
        if(title) f.title = title;
        if(icon)  f.icon  = icon;
        f.show_in_menu = show;
        if(newParent !== f.parent_table_id){
          var node = removeNode(a.tables, id);
          if(!node) return;
          node.parent_table_id = newParent||null;
          if(newParent){
            var pn = findNode(a.tables, newParent);
            if(pn){ pn.children.push(node); }
            else { a.tables.push(node); node.parent_table_id=null; }
          } else { a.tables.push(node); }
          reindex(a.tables, null);
        }
      });
    }
    drawerClose();
    render();
  }

  function dragStart(e, type, id, appId){
    _drag = {type:type, id:id, appId:appId};
    e.dataTransfer.effectAllowed='move';
    e.dataTransfer.setData('text/plain', id);
    e.stopPropagation();
    setTimeout(function(){
      var el = type==='app' ? document.querySelector('.me-app[data-app-id="'+id+'"]') : document.querySelector('.me-row[data-row="'+id+'"]');
      if(el) el.style.opacity='0.4';
    },0);
  }
  function dragEnd(e){
    document.querySelectorAll('.me-app').forEach(function(el){ el.style.opacity=''; el.classList.remove('drag-over-app'); });
    document.querySelectorAll('.me-row').forEach(function(el){ el.style.opacity=''; el.classList.remove('drag-over-before','drag-over-child','drag-over-after'); });
    _drag=null;
  }
  function dragOverApp(e, targetAppId){
    if(!_drag || _drag.type!=='app' || _drag.id===targetAppId) return;
    e.preventDefault(); e.stopPropagation();
    var el = document.querySelector('.me-app[data-app-id="'+targetAppId+'"]');
    if(el) el.classList.add('drag-over-app');
  }
  function dragLeaveApp(e){
    var el = e.currentTarget.closest('.me-app');
    if(el) el.classList.remove('drag-over-app');
  }
  function dropApp(e, targetAppId){
    e.preventDefault(); e.stopPropagation();
    if(!_drag || _drag.type!=='app' || _drag.id===targetAppId) return;
    var from = _data.findIndex(function(a){ return a.id===_drag.id; });
    var to   = _data.findIndex(function(a){ return a.id===targetAppId; });
    if(from<0||to<0) return;
    var moved = _data.splice(from,1)[0];
    _data.splice(to,0,moved);
    _data.forEach(function(a,i){ a.menu_order=i; });
    render();
  }
  function dragOverRow(e, targetId){
    if(!_drag || _drag.type!=='table' || parseInt(targetId)===_drag.id) return;
    e.preventDefault(); e.stopPropagation();
    var row = e.currentTarget;
    var rect = row.getBoundingClientRect();
    var pct  = (e.clientY - rect.top) / rect.height;
    row.classList.remove('drag-over-before','drag-over-child','drag-over-after');
    if(pct < 0.28) row.classList.add('drag-over-before');
    else if(pct < 0.72) row.classList.add('drag-over-child');
    else row.classList.add('drag-over-after');
  }
  function dragLeaveRow(e){
    e.currentTarget.classList.remove('drag-over-before','drag-over-child','drag-over-after');
  }
  function dropRow(e, type, targetId, targetAppId){
    e.preventDefault(); e.stopPropagation();
    if(!_drag || _drag.type!=='table' || parseInt(targetId)===_drag.id) return;
    targetId = parseInt(targetId); targetAppId = parseInt(targetAppId);
    var row = e.currentTarget;
    var rect = row.getBoundingClientRect();
    var pct  = (e.clientY - rect.top) / rect.height;
    row.classList.remove('drag-over-before','drag-over-child','drag-over-after');
    var srcApp = appOf(_drag.id);
    var dstApp = _data.find(function(a){ return a.id===targetAppId; });
    if(!srcApp||!dstApp) return;
    var dragNode = findNode(srcApp.tables, _drag.id);
    if(!dragNode || findNode([dragNode], targetId)) return;
    removeNode(srcApp.tables, _drag.id);
    var targetParentList = findParentList(dstApp.tables, targetId) || dstApp.tables;
    var ti = targetParentList.findIndex(function(n){ return n.id===targetId; });
    if(pct < 0.28){
      dragNode.parent_table_id = _listParentId(dstApp.tables, targetParentList);
      targetParentList.splice(ti, 0, dragNode);
    } else if(pct < 0.72){
      var targetNode = findNode(dstApp.tables, targetId);
      dragNode.parent_table_id = targetId;
      targetNode.children.push(dragNode);
    } else {
      dragNode.parent_table_id = _listParentId(dstApp.tables, targetParentList);
      targetParentList.splice(ti+1, 0, dragNode);
    }
    reindex(dstApp.tables, null);
    render();
  }
  function _listParentId(allTables, list){
    if(list === allTables) return null;
    var result = null;
    function search(nodes){
      for(var i=0;i<nodes.length;i++){
        if(nodes[i].children===list){ result=nodes[i].id; return true; }
        if(search(nodes[i].children)) return true;
      }
    }
    search(allTables);
    return result;
  }

  function save(){
    var btn = document.querySelector('[onclick="ME.save()"]');
    var oldHtml = btn.innerHTML;
    btn.disabled=true; btn.innerHTML='<i class="ti-reload mr-1"></i>Saving…';
    var csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    fetch('/admin/settings/menu/save',{
      method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf},
      body: JSON.stringify({apps:_data})
    }).then(function(r){ return r.json(); }).then(function(d){
      btn.disabled=false; btn.innerHTML=oldHtml;
      if(d.ok){
        btn.innerHTML='<i class="ti-check mr-1"></i>Saved!';
        setTimeout(function(){ btn.innerHTML=oldHtml; },2000);
      } else { arasNotify('Save error: '+(d.error||'unknown'), 'error'); }
    }).catch(function(err){ btn.disabled=false; btn.innerHTML=oldHtml; arasNotify('Save failed: '+String(err), 'error'); });
  }

  function load(){
    var root = document.getElementById('menuEditorRoot');
    if(root) root.innerHTML='<div class="text-muted p-3"><i class="ti-reload mr-1"></i>Loading…</div>';
    fetch('/admin/settings/menu/data').then(function(r){ return r.json(); }).then(function(d){ _data=d; render(); })
    .catch(function(){ if(root) root.innerHTML='<div class="text-danger p-3">Failed to load menu data.</div>'; });
  }

  function openAddModal(type){
    var modal = document.getElementById('meAddModal');
    document.getElementById('meAddModal_title').textContent = type === 'group' ? 'Add Menu Group' : 'Add Menu Page';
    document.getElementById('meAdd_type').value = type;
    document.getElementById('meAdd_title').value = '';
    document.getElementById('meAdd_icon').value = type === 'group' ? 'fa-folder' : 'fa-file';
    document.getElementById('meAdd_url').value = '';
    document.getElementById('meAdd_url_row').style.display = type === 'page' ? '' : 'none';
    document.getElementById('meAdd_parent_row').style.display = type === 'page' ? '' : 'none';
    var appSel = document.getElementById('meAdd_app'); appSel.innerHTML = '';
    (_data||[]).forEach(function(a){ var opt = document.createElement('option'); opt.value = a.id; opt.text = a.title; appSel.appendChild(opt); });
    if(type === 'page'){
      var parSel = document.getElementById('meAdd_parent'); parSel.innerHTML = '<option value="">— top level —</option>';
      function addParentOpts(nodes, depth){
        (nodes||[]).forEach(function(n){ if(n.is_group){ var opt = document.createElement('option'); opt.value = n.id; opt.text = '    '.repeat(depth) + n.title; parSel.appendChild(opt); addParentOpts(n.children, depth+1); } });
      }
      (_data||[]).forEach(function(a){ addParentOpts(a.tables, 0); });
    }
    modal.style.display = 'flex';
  }
  function closeAddModal(){ document.getElementById('meAddModal').style.display = 'none'; }
  function submitAdd(){
    var type = document.getElementById('meAdd_type').value;
    var body = {app_id: parseInt(document.getElementById('meAdd_app').value), title: document.getElementById('meAdd_title').value.trim(), icon: document.getElementById('meAdd_icon').value.trim()};
    if(type === 'page'){ body.url_suffix = document.getElementById('meAdd_url').value.trim(); body.parent_id = parseInt(document.getElementById('meAdd_parent').value)||null; }
    if(!body.title || (type==='page' && !body.url_suffix)){ arasNotify('Required fields missing.', 'error'); return; }
    var csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    fetch(type==='group'?'/admin/settings/menu/add-group':'/admin/settings/menu/add-page', {
      method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken': csrf}, body: JSON.stringify(body)
    }).then(function(r){ return r.json(); }).then(function(d){ if(d.ok){ closeAddModal(); load(); } else { arasNotify('Error: '+(d.error||'unknown'), 'error'); } });
  }

  async function deleteItem(e, id){
    e.stopPropagation(); if(!await confirm('Delete this menu item?')) return;
    var csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    fetch('/admin/settings/menu/delete/'+id, { method: 'POST', headers: {'X-CSRFToken': csrf} }).then(function(r){ return r.json(); }).then(function(d){ if(d.ok) load(); });
  }

  return {
    load: load, save: save, render: render,
    rowClick: function(e, type, id){ e.stopPropagation(); drawerOpen(type, id); },
    toggleKids: toggleKids, toggleApp: toggleApp, drawerClose: drawerClose, drawerApply: drawerApply,
    dragStart: dragStart, dragEnd: dragEnd, dragOverApp: dragOverApp, dragLeaveApp: dragLeaveApp, dropApp: dropApp,
    dragOverRow: dragOverRow, dragLeaveRow: dragLeaveRow, dropRow: dropRow,
    openAddModal: openAddModal, closeAddModal: closeAddModal, submitAdd: submitAdd, deleteItem: deleteItem,
  };
})();
