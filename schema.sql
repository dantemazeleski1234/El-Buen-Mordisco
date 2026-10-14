-- =============================================================================
-- SISTEMA DE GESTIÓN: EL BUEN MORDISCO
-- Archivo: schema.sql
-- Descripción: Script SQL puro (DDL y DML) con la estructura de la base de datos
-- y la carga de datos iniciales para la presentación en la facultad.
-- =============================================================================

-- Desactivar y activar claves foráneas para limpieza segura
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS venta;
DROP TABLE IF EXISTS detalle_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS producto;
DROP TABLE IF EXISTS proveedor;
DROP TABLE IF EXISTS cliente;
DROP TABLE IF EXISTS usuario;

PRAGMA foreign_keys = ON;

-- =============================================================================
-- 1. TABLA: USUARIO
-- =============================================================================
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL DEFAULT 'Cajero' -- 'Admin', 'Cajero', 'Cocina'
);

-- =============================================================================
-- 2. TABLA: CLIENTE
-- =============================================================================
CREATE TABLE cliente (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    telefono VARCHAR(30),
    email VARCHAR(120) UNIQUE,
    password VARCHAR(255) NOT NULL,
    direccion VARCHAR(200)
);

-- =============================================================================
-- 3. TABLA: PROVEEDOR
-- =============================================================================
CREATE TABLE proveedor (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(30),
    email VARCHAR(120),
    direccion VARCHAR(200)
);

-- =============================================================================
-- 4. TABLA: PRODUCTO
-- =============================================================================
CREATE TABLE producto (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proveedor INTEGER,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    categoria VARCHAR(50) NOT NULL, -- 'Hamburguesas', 'Papas', 'Bebidas', 'Postres'
    disponible BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (id_proveedor) REFERENCES proveedor(id_proveedor) ON DELETE SET NULL
);

-- =============================================================================
-- 5. TABLA: STOCK
-- =============================================================================
CREATE TABLE stock (
    id_stock INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 0,
    fecha_actualizacion DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_producto) REFERENCES producto(id_producto) ON DELETE CASCADE
);

-- =============================================================================
-- 6. TABLA: PEDIDO
-- =============================================================================
CREATE TABLE pedido (
    id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    hora TIME NOT NULL DEFAULT (time('now', 'localtime')),
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente', -- 'Pendiente', 'En Preparación', 'Listo', 'Entregado'
    total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    metodo_pago VARCHAR(50) NOT NULL DEFAULT 'Efectivo', -- 'Efectivo', 'Tarjeta', 'MercadoPago'
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE SET NULL
);

-- =============================================================================
-- 7. TABLA: DETALLE_PEDIDO
-- =============================================================================
CREATE TABLE detalle_pedido (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES producto(id_producto)
);

-- =============================================================================
-- 8. TABLA: VENTA
-- =============================================================================
CREATE TABLE venta (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    total DECIMAL(10, 2) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    comprobante VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- =============================================================================
-- DATOS INICIALES DEMOSTRATIVOS (DML: INSERT INTO)
-- =============================================================================

-- Usuario Inicial y Roles Demostrativos para la Exposición
INSERT INTO usuario (nombre, apellido, email, password, rol) VALUES
('admin', '', 'admin@gmail.com', 'admin123', 'Admin'),
('cajero', '', 'cajero@gmail.com', 'cajero123', 'Cajero'),
('cocinero', '', 'cocinero@gmail.com', 'cocinero123', 'Cocina');

-- Proveedor Inicial
INSERT INTO proveedor (nombre, telefono, email, direccion) 
VALUES ('Distribuidora Central de Carnes y Panes', '11-4567-8900', 'ventas@distribuidoracentral.com', 'Av. San Martín 1540');

-- Menú Inicial de Hamburguesas, Acompañamientos y Bebidas
INSERT INTO producto (id_proveedor, nombre, descripcion, precio, categoria, disponible) VALUES
(1, 'Hamburguesa Clásica', 'Medallón de carne 120g, queso cheddar, lechuga, tomate y mayonesa de la casa.', 4500.00, 'Hamburguesas', 1),
(1, 'Doble Cheddar & Bacon', 'Doble medallón de carne 240g, cuatro fetas de cheddar y crocante panceta ahumada.', 6300.00, 'Hamburguesas', 1),
(1, 'Crispy Chicken Burger', 'Pechuga crujiente rebozada en cereales, lechuga fresca y salsa tártara artesanal.', 5400.00, 'Hamburguesas', 1),
(1, 'Papas Fritas Clásicas', 'Porción abundante de bastones de papas fritas doradas y crocantes.', 2600.00, 'Papas', 1),
(1, 'Papas Mordisco Especial', 'Bañadas en salsa cheddar caliente con lluvia de panceta crocante y verdeo.', 3900.00, 'Papas', 1),
(1, 'Gaseosa Línea Cola 500ml', 'Botella individual bien fría.', 1800.00, 'Bebidas', 1),
(1, 'Agua Mineral Sin Gas 500ml', 'Botella individual.', 1500.00, 'Bebidas', 1),
(1, 'Cerveza Artesanal IPA 473ml', 'Lata de cerveza rubia artesanal lupulada bien helada.', 3200.00, 'Bebidas', 1),
(1, 'Sundae de Dulce de Leche', 'Helado suave de vainilla con salsa caliente de dulce de leche y maní.', 2400.00, 'Postres', 1);

-- Stock Inicial para cada producto
INSERT INTO stock (id_producto, cantidad) VALUES
(1, 50),
(2, 40),
(3, 35),
(4, 60),
(5, 45),
(6, 100),
(7, 50),
(8, 40),
(9, 30);
