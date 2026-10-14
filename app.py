"""
=============================================================================
SISTEMA DE GESTIÓN: EL BUEN MORDISCO
Archivo: app.py (CON AUTENTICACIÓN, ROLES Y SQL PURO)
Descripción: Servidor web Flask con:
  - Pantalla de inicio de sesión (Login) con diseño dividido 50/50.
  - Control de Acceso Basado en Roles (RBAC): Admin, Cajero, Cocina.
  - Consultas SQL puras (SELECT, INSERT, UPDATE) con sqlite3.
=============================================================================
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from db import get_db_connection, init_db
import json
import os

app = Flask(__name__)
# Clave secreta para firmar las cookies de sesión y mensajes flash
app.secret_key = 'el_buen_mordisco_clave_sql_2026'


# =============================================================================
# DECORADOR DE SEGURIDAD: CONTROL DE ACCESO POR ROLES (RBAC)
# Protege las rutas para que nadie entre sin iniciar sesión o a secciones indebidas.
# =============================================================================
def login_required(roles_permitidos=None):
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            # 1. Verificar si el usuario inició sesión
            if 'usuario_id' not in session:
                flash('Debes iniciar sesión para acceder al sistema.', 'warning')
                return redirect(url_for('login'))
            
            # 2. Verificar si su rol tiene permiso para esta pantalla
            if roles_permitidos and session.get('rol') not in roles_permitidos:
                flash(f'Acceso denegado: El rol "{session.get("rol")}" no tiene permisos para esa sección.', 'danger')
                # Redirección inteligente al lugar de trabajo correspondiente
                if session.get('rol') == 'Cocina':
                    return redirect(url_for('cocina'))
                return redirect(url_for('pos'))
                
            return f(*args, **kwargs)
        return funcion_decorada
    return decorador


# =============================================================================
# 1. RUTA RAIZ ('/')
# Redirige al menú si es cliente, o al login de clientes.
# =============================================================================
@app.route('/')
def index():
    if 'cliente_id' in session:
        return redirect(url_for('menu'))
    # Si hay un usuario del personal (por si acaso), lo manda a su panel
    if 'usuario_id' in session:
        if session.get('rol') == 'Cocina':
            return redirect(url_for('cocina'))
        return redirect(url_for('pos'))
    return redirect(url_for('login_cliente'))


# =============================================================================
# 2. RUTA SECRETA DEL PERSONAL ('/personal')
# Procesa las credenciales y redirige según el rol (Admin, Cajero, Cocina).
# =============================================================================
@app.route('/personal', methods=['GET', 'POST'])
def login():
    # Si ya tiene una sesión abierta, lo mandamos directo a su pantalla
    if request.method == 'GET' and 'usuario_id' in session:
        if session.get('rol') == 'Cocina':
            return redirect(url_for('cocina'))
        return redirect(url_for('pos'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        query = "SELECT * FROM usuario WHERE email = ? AND password = ?;"
        usuario = conn.execute(query, (email, password)).fetchone()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario['id_usuario']
            session['nombre'] = usuario['nombre']
            session['apellido'] = usuario['apellido']
            session['email'] = usuario['email']
            session['rol'] = usuario['rol']

            flash(f'¡Bienvenido {usuario["nombre"]}! Has ingresado como {usuario["rol"]}.', 'success')
            if usuario['rol'] == 'Cocina':
                return redirect(url_for('cocina'))
            return redirect(url_for('pos'))
        else:
            flash('Usuario o contraseña incorrectos. Revisa tus datos.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


# =============================================================================
# 2.1 RUTA: LOGIN CLIENTES ('/login_cliente')
# =============================================================================
@app.route('/login_cliente', methods=['GET', 'POST'])
def login_cliente():
    if 'cliente_id' in session:
        return redirect(url_for('menu'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        query = "SELECT * FROM cliente WHERE email = ? AND password = ?;"
        cliente = conn.execute(query, (email, password)).fetchone()
        conn.close()

        if cliente:
            session['cliente_id'] = cliente['id_cliente']
            session['cliente_nombre'] = cliente['nombre']
            session['cliente_telefono'] = cliente['telefono']
            flash(f'¡Bienvenido {cliente["nombre"]}! Ya puedes hacer tu pedido.', 'success')
            return redirect(url_for('menu'))
        else:
            flash('Email o contraseña incorrectos. Si no tienes cuenta, regístrate.', 'danger')
            return render_template('login_cliente.html')

    return render_template('login_cliente.html')


# =============================================================================
# 2.2 RUTA: REGISTRO CLIENTES ('/registro')
# =============================================================================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        direccion = request.form.get('direccion', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id_cliente FROM cliente WHERE email = ?;", (email,))
        if cursor.fetchone():
            flash('Ese correo ya está registrado. Por favor, inicia sesión.', 'warning')
            conn.close()
            return redirect(url_for('login_cliente'))

        try:
            cursor.execute(
                """
                INSERT INTO cliente (nombre, apellido, telefono, email, password, direccion)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (nombre, apellido, telefono, email, password, direccion)
            )
            conn.commit()
            flash('¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login_cliente'))
        except Exception as e:
            conn.rollback()
            flash(f'Error al registrarse: {str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('registro_cliente.html')


# =============================================================================
# 3. RUTA: CERRAR SESIÓN ('/logout')
# Destruye la sesión actual y redirige.
# =============================================================================
@app.route('/logout')
def logout():
    es_personal = 'usuario_id' in session
    nombre = session.get('nombre', session.get('cliente_nombre', 'Usuario'))
    session.clear()
    flash(f'Hasta luego {nombre}. Has cerrado sesión correctamente.', 'info')
    
    if es_personal:
        return redirect(url_for('login')) # login de personal
    else:
        return redirect(url_for('login_cliente'))


# =============================================================================
# 4. RUTA: PUNTO DE VENTA ('/pos')
# Acceso para Cajero y Administrador.
# =============================================================================
@app.route('/pos')
@login_required(roles_permitidos=['Admin', 'Cajero'])
def pos():
    conn = get_db_connection()
    query = """
        SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.categoria, p.disponible,
               COALESCE(s.cantidad, 0) AS stock_cantidad
        FROM producto p
        LEFT JOIN stock s ON p.id_producto = s.id_producto
        WHERE p.disponible = 1
        ORDER BY p.categoria, p.nombre;
    """
    productos = conn.execute(query).fetchall()
    conn.close()
    return render_template('pos.html', productos=productos)


# =============================================================================
# 5. RUTA: CREAR PEDIDO (Toma de comanda y facturación)
# Registra la venta asociando el ID del usuario actualmente conectado.
# =============================================================================
@app.route('/crear_pedido', methods=['POST'])
@login_required(roles_permitidos=['Admin', 'Cajero'])
def crear_pedido():
    cliente_nombre = request.form.get('cliente_nombre', '').strip()
    cliente_telefono = request.form.get('cliente_telefono', '').strip()
    metodo_pago = request.form.get('metodo_pago', 'Efectivo')
    items_json = request.form.get('items_json', '[]')

    items = json.loads(items_json)
    if not items:
        flash('El carrito está vacío. Agrega al menos un producto.', 'warning')
        return redirect(url_for('pos'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. SQL: Buscar o registrar al Cliente
        id_cliente = None
        if cliente_nombre:
            cursor.execute("SELECT id_cliente FROM cliente WHERE nombre = ?;", (cliente_nombre,))
            cliente_existente = cursor.fetchone()
            
            if cliente_existente:
                id_cliente = cliente_existente['id_cliente']
            else:
                # Se asigna una contraseña vacía o por defecto para clientes de mostrador
                cursor.execute(
                    "INSERT INTO cliente (nombre, apellido, telefono, password) VALUES (?, '', ?, '');",
                    (cliente_nombre, cliente_telefono)
                )
                id_cliente = cursor.lastrowid

        # 2. Calcular total
        total_pedido = sum(item['precio'] * item['cantidad'] for item in items)

        # 3. SQL: INSERT INTO pedido
        cursor.execute(
            """
            INSERT INTO pedido (id_cliente, fecha, hora, estado, total, metodo_pago)
            VALUES (?, CURRENT_DATE, time('now', 'localtime'), 'Pendiente', ?, ?);
            """,
            (id_cliente, total_pedido, metodo_pago)
        )
        id_pedido = cursor.lastrowid

        # 4. Detalle y Stock
        for item in items:
            subtotal = item['precio'] * item['cantidad']
            cursor.execute(
                """
                INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?);
                """,
                (id_pedido, item['id'], item['cantidad'], item['precio'], subtotal)
            )

            cursor.execute(
                """
                UPDATE stock
                SET cantidad = cantidad - ?, fecha_actualizacion = CURRENT_DATE
                WHERE id_producto = ? AND cantidad >= ?;
                """,
                (item['cantidad'], item['id'], item['cantidad'])
            )

        # 5. SQL: Venta registrada por el usuario con sesión activa
        id_usuario_actual = session.get('usuario_id', 1)
        comprobante = f"TICK-{id_pedido:04d}"

        cursor.execute(
            """
            INSERT INTO venta (id_pedido, id_usuario, fecha, total, metodo_pago, comprobante)
            VALUES (?, ?, CURRENT_DATE, ?, ?, ?);
            """,
            (id_pedido, id_usuario_actual, total_pedido, metodo_pago, comprobante)
        )

        conn.commit()
        flash(f'¡Pedido #{id_pedido} registrado y enviado a cocina! Comprobante: {comprobante}', 'success')
        return redirect(url_for('cocina'))

    except Exception as e:
        conn.rollback()
        flash(f'Error al procesar el pedido con SQL: {str(e)}', 'danger')
        return redirect(url_for('pos'))
    finally:
        conn.close()


# =============================================================================
# 6. RUTA: COCINA / COMANDERA
# Acceso para Cocina, Cajero y Administrador.
# =============================================================================
@app.route('/cocina')
@login_required(roles_permitidos=['Admin', 'Cajero', 'Cocina'])
def cocina():
    conn = get_db_connection()

    def obtener_pedidos_por_estado(estado):
        query = """
            SELECT p.id_pedido, p.fecha, p.hora, p.estado, p.total,
                   COALESCE(c.nombre, 'Consumidor Final') AS cliente_nombre
            FROM pedido p
            LEFT JOIN cliente c ON p.id_cliente = c.id_cliente
            WHERE p.estado = ?
            ORDER BY p.id_pedido ASC;
        """
        pedidos = conn.execute(query, (estado,)).fetchall()
        
        resultado = []
        for ped in pedidos:
            query_detalles = """
                SELECT dp.cantidad, dp.precio_unitario, dp.subtotal, prod.nombre AS producto_nombre
                FROM detalle_pedido dp
                JOIN producto prod ON dp.id_producto = prod.id_producto
                WHERE dp.id_pedido = ?;
            """
            detalles = conn.execute(query_detalles, (ped['id_pedido'],)).fetchall()
            ped_dict = dict(ped)
            ped_dict['detalles'] = detalles
            resultado.append(ped_dict)
            
        return resultado

    pedidos_pendientes = obtener_pedidos_por_estado('Pendiente')
    pedidos_preparacion = obtener_pedidos_por_estado('En Preparación')
    pedidos_listos = obtener_pedidos_por_estado('Listo')

    conn.close()
    return render_template(
        'cocina.html',
        pedidos_pendientes=pedidos_pendientes,
        pedidos_preparacion=pedidos_preparacion,
        pedidos_listos=pedidos_listos
    )


# =============================================================================
# 7. RUTA: CAMBIAR ESTADO DE UN PEDIDO
# =============================================================================
@app.route('/cambiar_estado/<int:id_pedido>/<string:nuevo_estado>')
@login_required(roles_permitidos=['Admin', 'Cajero', 'Cocina'])
def cambiar_estado(id_pedido, nuevo_estado):
    estados_validos = ['Pendiente', 'En Preparación', 'Listo', 'Entregado', 'Cancelado']
    if nuevo_estado in estados_validos:
        conn = get_db_connection()
        conn.execute(
            "UPDATE pedido SET estado = ? WHERE id_pedido = ?;",
            (nuevo_estado, id_pedido)
        )
        conn.commit()
        conn.close()
        flash(f'Pedido #{id_pedido} actualizado a: "{nuevo_estado}".', 'info')
    
    return redirect(url_for('cocina'))


# =============================================================================
# 8. RUTA: GESTIÓN DE PRODUCTOS Y STOCK (Solo Administrador)
# =============================================================================
@app.route('/productos')
@login_required(roles_permitidos=['Admin'])
def productos():
    conn = get_db_connection()
    query = """
        SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.categoria, p.disponible,
               COALESCE(s.cantidad, 0) AS stock_cantidad,
               COALESCE(pr.nombre, 'General') AS proveedor_nombre
        FROM producto p
        LEFT JOIN stock s ON p.id_producto = s.id_producto
        LEFT JOIN proveedor pr ON p.id_proveedor = pr.id_proveedor
        ORDER BY p.id_producto ASC;
    """
    lista_productos = conn.execute(query).fetchall()
    conn.close()
    return render_template('productos.html', productos=lista_productos)


# =============================================================================
# 9. RUTA: CREAR NUEVO PRODUCTO (Solo Administrador)
# =============================================================================
@app.route('/crear_producto', methods=['POST'])
@login_required(roles_permitidos=['Admin'])
def crear_producto():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    categoria = request.form.get('categoria')
    precio = float(request.form.get('precio', 0))
    stock_inicial = int(request.form.get('stock_inicial', 0))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id_proveedor FROM proveedor LIMIT 1;")
    prov = cursor.fetchone()
    id_proveedor = prov['id_proveedor'] if prov else None

    cursor.execute(
        """
        INSERT INTO producto (id_proveedor, nombre, descripcion, precio, categoria, disponible)
        VALUES (?, ?, ?, ?, ?, 1);
        """,
        (id_proveedor, nombre, descripcion, precio, categoria)
    )
    id_nuevo_producto = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO stock (id_producto, cantidad, fecha_actualizacion)
        VALUES (?, ?, CURRENT_DATE);
        """,
        (id_nuevo_producto, stock_inicial)
    )

    conn.commit()
    conn.close()

    flash(f'Producto "{nombre}" agregado exitosamente mediante SQL INSERT.', 'success')
    return redirect(url_for('productos'))


# =============================================================================
# 10. RUTA: EDITAR PRODUCTO (Solo Administrador)
# =============================================================================
@app.route('/editar_producto/<int:id_producto>', methods=['POST'])
@login_required(roles_permitidos=['Admin'])
def editar_producto(id_producto):
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = float(request.form.get('precio', 0))
    cantidad = int(request.form.get('cantidad', 0))

    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE producto
            SET nombre = ?, descripcion = ?, precio = ?
            WHERE id_producto = ?;
            """,
            (nombre, descripcion, precio, id_producto)
        )
        conn.execute(
            """
            UPDATE stock
            SET cantidad = ?, fecha_actualizacion = CURRENT_DATE
            WHERE id_producto = ?;
            """,
            (cantidad, id_producto)
        )
        conn.commit()
        flash(f'Producto "{nombre}" actualizado correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al editar producto: {str(e)}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('productos'))


# =============================================================================
# 11. RUTA: VISIBILIDAD DE PRODUCTO (Solo Administrador)
# =============================================================================
@app.route('/toggle_disponible/<int:id_producto>')
@login_required(roles_permitidos=['Admin'])
def toggle_disponible(id_producto):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE producto
        SET disponible = CASE WHEN disponible = 1 THEN 0 ELSE 1 END
        WHERE id_producto = ?;
        """,
        (id_producto,)
    )
    conn.commit()
    conn.close()
    flash('Visibilidad del producto actualizada con éxito.', 'info')
    return redirect(url_for('productos'))



# =============================================================================
# 11.B RUTA: ELIMINAR PRODUCTO (Solo Administrador)
# =============================================================================
@app.route('/eliminar_producto/<int:id_producto>', methods=['POST'])
@login_required(roles_permitidos=['Admin'])
def eliminar_producto(id_producto):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM producto WHERE id_producto = ?;", (id_producto,))
        conn.commit()
        flash('Producto eliminado permanentemente de la base de datos.', 'success')
    except Exception as e:
        conn.rollback()
        # Capturamos el error de integridad referencial de SQLite si ya tiene pedidos
        flash('No se puede eliminar este producto porque ya tiene ventas registradas. Te recomendamos ocultarlo (con el botón del ojito) para no romper el historial.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('productos'))

# =============================================================================
# 12. RUTA: HISTORIAL DE VENTAS Y FACTURACIÓN (Solo Administrador)
# =============================================================================
@app.route('/ventas')
@login_required(roles_permitidos=['Admin'])
def ventas():
    conn = get_db_connection()
    query = """
        SELECT v.id_venta, v.fecha, v.total, v.metodo_pago, v.comprobante, v.id_pedido,
               COALESCE(u.nombre, 'Cajero') AS usuario_nombre,
               COALESCE(c.nombre, 'Consumidor Final') AS cliente_nombre
        FROM venta v
        LEFT JOIN usuario u ON v.id_usuario = u.id_usuario
        LEFT JOIN pedido p ON v.id_pedido = p.id_pedido
        LEFT JOIN cliente c ON p.id_cliente = c.id_cliente
        ORDER BY v.id_venta DESC;
    """
    ventas_list = conn.execute(query).fetchall()

    query_total = "SELECT COALESCE(SUM(total), 0) AS total_acumulado FROM venta;"
    total_recaudado = conn.execute(query_total).fetchone()['total_acumulado']

    conn.close()
    return render_template('ventas.html', ventas=ventas_list, total_recaudado=total_recaudado)


# =============================================================================
# 13. RUTA: MENÚ PÚBLICO PARA CLIENTES ('/menu')
# Permite a los clientes ver los platos y armar su pedido (Requiere sesión).
# =============================================================================
@app.route('/menu')
def menu():
    if 'cliente_id' not in session:
        flash('Debes iniciar sesión para ver el menú y hacer tu pedido.', 'warning')
        return redirect(url_for('login_cliente'))

    conn = get_db_connection()
    query = """
        SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.categoria, p.disponible,
               COALESCE(s.cantidad, 0) AS stock_cantidad
        FROM producto p
        LEFT JOIN stock s ON p.id_producto = s.id_producto
        WHERE p.disponible = 1
        ORDER BY p.categoria, p.nombre;
    """
    productos = conn.execute(query).fetchall()
    conn.close()
    return render_template('menu_cliente.html', productos=productos)


# =============================================================================
# 14. RUTA: PROCESAR PEDIDO DEL CLIENTE ('/cliente/pedido')
# Recibe el pedido online, descuenta stock y lo envía directo a la cocina.
# =============================================================================
@app.route('/cliente/pedido', methods=['POST'])
def crear_pedido_cliente():
    # Solo pueden pedir si iniciaron sesión
    if 'cliente_id' not in session:
        flash('Por favor inicia sesión para hacer tu pedido.', 'warning')
        return redirect(url_for('login_cliente'))

    id_cliente = session['cliente_id']
    modalidad = request.form.get('modalidad', 'Para comer acá')
    metodo_pago = request.form.get('metodo_pago', 'Efectivo en Mostrador')
    items_json = request.form.get('items_json', '[]')

    items = json.loads(items_json)
    if not items:
        flash('El carrito está vacío. Agrega productos a tu pedido.', 'warning')
        return redirect(url_for('menu'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # 2. Calcular total
        total_pedido = sum(item['precio'] * item['cantidad'] for item in items)

        # 3. Guardar pedido en estado Pendiente
        info_pago = f"{metodo_pago} ({modalidad})"
        cursor.execute(
            """
            INSERT INTO pedido (id_cliente, fecha, hora, estado, total, metodo_pago)
            VALUES (?, CURRENT_DATE, time('now', 'localtime'), 'Pendiente', ?, ?);
            """,
            (id_cliente, total_pedido, info_pago)
        )
        id_pedido = cursor.lastrowid

        # 4. Registrar detalle_pedido y descontar stock
        for item in items:
            subtotal = item['precio'] * item['cantidad']
            cursor.execute(
                """
                INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?);
                """,
                (id_pedido, item['id'], item['cantidad'], item['precio'], subtotal)
            )

            cursor.execute(
                """
                UPDATE stock
                SET cantidad = cantidad - ?, fecha_actualizacion = CURRENT_DATE
                WHERE id_producto = ? AND cantidad >= ?;
                """,
                (item['cantidad'], item['id'], item['cantidad'])
            )

        # 5. Generar comprobante de venta WEB
        cursor.execute("SELECT id_usuario FROM usuario WHERE rol = 'Admin' LIMIT 1;")
        admin = cursor.fetchone()
        id_usuario = admin['id_usuario'] if admin else 1
        comprobante = f"WEB-{id_pedido:04d}"

        cursor.execute(
            """
            INSERT INTO venta (id_pedido, id_usuario, fecha, total, metodo_pago, comprobante)
            VALUES (?, ?, CURRENT_DATE, ?, ?, ?);
            """,
            (id_pedido, id_usuario, total_pedido, info_pago, comprobante)
        )

        conn.commit()
        return redirect(url_for('pedido_confirmado', id_pedido=id_pedido))

    except Exception as e:
        conn.rollback()
        flash(f'Error al procesar tu pedido: {str(e)}', 'danger')
        return redirect(url_for('menu'))
    finally:
        conn.close()


# =============================================================================
# 15. RUTA: TICKET DE CONFIRMACIÓN DEL CLIENTE
# =============================================================================
@app.route('/pedido_confirmado/<int:id_pedido>')
def pedido_confirmado(id_pedido):
    conn = get_db_connection()
    query_pedido = """
        SELECT p.*, COALESCE(c.nombre, 'Cliente') AS cliente_nombre,
               COALESCE(c.telefono, '') AS cliente_telefono
        FROM pedido p
        LEFT JOIN cliente c ON p.id_cliente = c.id_cliente
        WHERE p.id_pedido = ?;
    """
    pedido = conn.execute(query_pedido, (id_pedido,)).fetchone()

    if not pedido:
        conn.close()
        return redirect(url_for('menu'))

    query_detalles = """
        SELECT dp.*, prod.nombre AS producto_nombre
        FROM detalle_pedido dp
        JOIN producto prod ON dp.id_producto = prod.id_producto
        WHERE dp.id_pedido = ?;
    """
    detalles = conn.execute(query_detalles, (id_pedido,)).fetchall()
    conn.close()

    cliente_data = {'nombre': pedido['cliente_nombre'], 'telefono': pedido['cliente_telefono']}
    return render_template('pedido_confirmado.html', pedido=pedido, cliente=cliente_data, detalles=detalles)


# =============================================================================
# INICIALIZACIÓN Y ARRANQUE
# =============================================================================
if __name__ == '__main__':
    if not os.path.exists('el_buen_mordisco.db'):
        init_db()

    print("\n" + "="*60)
    print("🍔 SISTEMA 'EL BUEN MORDISCO' (CON LOGIN Y ROLES) INICIADO")
    print("👉 Abre tu navegador web en: http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    app.run(debug=True)
