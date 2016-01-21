/* $RCSfile$
 * $Author: hansonr $
 * $Date: 2009-06-05 07:42:12 -0500 (Fri, 05 Jun 2009) $
 * $Revision: 10958 $
 *
 * Copyright (C) 2003-2005  The Jmol Development Team
 *
 * Contact: jmol-developers@lists.sf.net
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Lesser General License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public
 *  License along with this library; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
 */

package org.jmol.script;

import java.util.Arrays;
import java.util.BitSet;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import javax.vecmath.Matrix3f;
import javax.vecmath.Matrix4f;
import javax.vecmath.Point3f;
import javax.vecmath.Point4f;
import javax.vecmath.Vector3f;

import org.jmol.modelset.Bond.BondSet;
import org.jmol.util.ArrayUtil;
import org.jmol.util.BitSetUtil;
import org.jmol.util.Escape;
import org.jmol.util.Parser;

import org.jmol.util.Measure;
import org.jmol.util.Quaternion;
import org.jmol.util.TextFormat;

public class ScriptVariable extends Token {

  final private static ScriptVariable vT = new ScriptVariable(on, 1, "true");
  final private static ScriptVariable vF = new ScriptVariable(off, 0, "false");
  final static ScriptVariable vAll = new ScriptVariable(all, "all");

  public int index = Integer.MAX_VALUE;

  private final static int FLAG_CANINCREMENT = 1;
  private final static int FLAG_LOCALVAR = 2;

  private int flags = ~FLAG_CANINCREMENT & FLAG_LOCALVAR;
  private String name;

  public ScriptVariable() {
    tok = string;
    value = "";
  }

  public ScriptVariable(int tok) {
    this.tok = tok;
  }

  public ScriptVariable(int tok, int intValue, Object value) {
    super(tok, intValue, value);
  }

  public ScriptVariable(int tok, Object value) {
    super(tok, value);
  }

  public ScriptVariable(int tok, int intValue) {
    super(tok, intValue);
  }

  public ScriptVariable(BitSet bs, int index) {
    value = bs;
    this.index = index;
    tok = bitset;
  }

  public ScriptVariable(Token theToken) {
    tok = theToken.tok;
    intValue = theToken.intValue;
    value = theToken.value;
  }
  
  static public boolean isVariableType(Object x) {
    return (x instanceof ScriptVariable
        || x instanceof BitSet
        || x instanceof Boolean
        || x instanceof Float
        || x instanceof Integer
        || x instanceof Point3f    // stored as point3f
        || x instanceof Vector3f   // stored as point3f
        || x instanceof Point4f    // stored as point4f
        || x instanceof Quaternion // stored as point4f
        || x instanceof String
        || x instanceof Map<?, ?>  // stored as Map<String, ScriptVariable>
        || x instanceof List<?>    // stored as list
        || x instanceof double[]   // stored as list
        || x instanceof float[]    // stored as list
        || x instanceof Float[]    // stored as list
        || x instanceof int[]      // stored as list
        || x instanceof String[]); // stored as list
  }

  static public String typeOf(ScriptVariable x) {
    int tok = (x == null ? nada : x.tok);
    switch (tok) {
    case on:
    case off:
      return "boolean";
    case bitset:
      return (x.value instanceof BondSet ? "bondset" : "bitset");
    case integer:
    case decimal:
    case point3f:
    case point4f:
    case string:
    case list:
    case hash:
    case matrix3f:
    case matrix4f:
      return astrType[tok];
    }
    return "?";
  }

  @SuppressWarnings("unchecked")
  public static int sizeOf(Token x) {
    switch (x == null ? nada : x.tok) {
    case bitset:
      return BitSetUtil.cardinalityOf(bsSelect(x));
    case on:
    case off:
      return -1;
    case integer:
      return -2;
    case decimal:
      return -4;
    case point3f:
      return -8;
    case point4f:
      return -16;
    case matrix3f:
      return -32;
    case matrix4f:
      return -64;
    case string:
      return ((String) x.value).length();
    case list:
      return x.intValue == Integer.MAX_VALUE ? ((String[]) x.value).length
          : sizeOf(selectItem(x));
    case hash:
      return ((Map<String, ScriptVariable>) x.value).size();
    default:
      return 0;
    }
  }

  public static ScriptVariable intVariable(int intValue) {
    return new ScriptVariable(integer, intValue);
  }

  /**
   * @param x
   * @return  a ScriptVariable of the input type, or if x is null, then a new ScriptVariable,
   *     or, if the type is not found, null
   */
  @SuppressWarnings("unchecked")
  public static ScriptVariable getVariable(Object x) {
    if (x == null)
      return new ScriptVariable();
    if (x instanceof ScriptVariable)
      return (ScriptVariable) x;
    
    // the eight basic types are:
    // boolean, integer, decimal, string, point3f, point4f, bitset, and list
    // listf is a special temporary type for storing results
    // of .all in preparation for .bin in the case of xxx.all.bin
    // but with some work, this could be developed into a storage class
    
    if (x instanceof Boolean)
      return getBoolean(((Boolean)x).booleanValue());
    if (x instanceof Integer)
      return new ScriptVariable(integer, ((Integer) x).intValue());
    if (x instanceof Float)
      return new ScriptVariable(decimal, x);
    if (x instanceof String) {
      x = unescapePointOrBitsetAsVariable((String) x);
      if (x instanceof ScriptVariable)
        return (ScriptVariable) x;
      return new ScriptVariable(string, x);
    }
    if (x instanceof Point3f)
      return new ScriptVariable(point3f, x);
    if (x instanceof Vector3f)
      return new ScriptVariable(point3f, new Point3f((Vector3f) x));
    if (x instanceof BitSet)
      return new ScriptVariable(bitset, x);
    if (x instanceof Point4f)
      return new ScriptVariable(point4f, x);
    // note: for quaternions, we save them {q1, q2, q3, q0} 
    // While this may seem odd, it is so that for any point4 -- 
    // planes, axisangles, and quaternions -- we can use the 
    // first three coordinates to determine the relavent axis
    // the fourth then gives us offset to {0,0,0} (plane), 
    // rotation angle (axisangle), and cos(theta/2) (quaternion).
    if (x instanceof Quaternion)
      return new ScriptVariable(point4f, ((Quaternion)x).toPoint4f());
    if (x instanceof Matrix3f)
      return new ScriptVariable(matrix3f, x);
    if (x instanceof Matrix4f)
      return new ScriptVariable(matrix4f, x);
    if (x instanceof String[])
      return new ScriptVariable(list, x);
    if (x instanceof Float[])
      return new ScriptVariable(listf, x);
    if (x instanceof Map) {
      Map<String, Object> ht = (Map<String, Object>)x; 
      Iterator<String> e = ht.keySet().iterator();
      while (e.hasNext()) {
        if (!(ht.get(e.next()) instanceof ScriptVariable)) {
          Map<String, ScriptVariable> x2 = new Hashtable<String, ScriptVariable>();
          for (Map.Entry<String, Object> entry: ht.entrySet()) {
            String key = entry.getKey();
            Object o = entry.getValue();
            x2.put(key, getVariable(isVariableType(o) ? o : Escape.toReadable(key, o)));
          }
          x = x2;
          break;
        }
      }
      return new ScriptVariable(hash, x);
    }
    
    
    // all the rest are stored as list
    
    if (x instanceof int[]) {
      int[] ix = (int[]) x;
      String[] s = new String[ix.length];
      for (int i = ix.length; --i >= 0; )
        s[i] = "" + ix[i];
      return new ScriptVariable(list, s);
    }
    if (x instanceof float[]) {
      float[] f = (float[]) x;
      String[] s = new String[f.length];
      for (int i = f.length; --i >= 0; )
        s[i] = "" + f[i];
      return new ScriptVariable(list, s);
    }
    if (x instanceof double[]) {
      double[] f = (double[]) x;
      String[] s = new String[f.length];
      for (int i = f.length; --i >= 0; )
        s[i] = "" + f[i];
      return new ScriptVariable(list, s);
    }
    
    if (x instanceof List) {
        // will be turned into list
        List<Object> v = (List<Object>) x;
        int len = v.size();
        String[] list = new String[len];
        for (int i = 0; i < len; i++) {
          Object o = v.get(i);
          if (o instanceof String)
            list[i] = (String) o;
          else
            list[i] = Escape.toReadable(o);
        }
        return getVariable(list);
    }
    return new ScriptVariable(string, Escape.toReadable(x));
  }

  @SuppressWarnings("unchecked")
  public ScriptVariable set(ScriptVariable v) {
    index = v.index;
    intValue = v.intValue;
    tok = v.tok;
    switch (tok) {
    case hash:
      value = new Hashtable<String, ScriptVariable>((Map<String, ScriptVariable>) v.value);
      break;
    case list:
      int n = ((String[])v.value).length;
      value = new String[n];
      System.arraycopy(v.value, 0, value, 0, n);
      break;
    default:
      value = v.value;
      break;
    }
    return this;
  }

  public ScriptVariable setName(String name) {
    this.name = name;
    flags |= FLAG_CANINCREMENT;
    //System.out.println("Variable: " + name + " " + intValue + " " + value);
    return this;
  }

  public ScriptVariable setGlobal() {
    flags &= ~FLAG_LOCALVAR;
    return this;
  }

  public boolean canIncrement() {
    return tokAttr(flags, FLAG_CANINCREMENT);
  }

  public boolean increment(int n) {
    if (!canIncrement())
      return false;
    switch (tok) {
    case integer:
      intValue += n;
      break;
    case decimal:
      value = new Float(((Float) value).floatValue() + n);
      break;
    default:
      value = nValue(this);
      if (value instanceof Integer) {
        tok = integer;
        intValue = ((Integer) value).intValue();
      } else {
        tok = decimal;
      }
    }
    return true;
  }

  public static ScriptVariable getVariableSelected(int index, Object value) {
    ScriptVariable v = new ScriptVariable(bitset, value);
    v.index = index;
    return v;
  }

  public boolean asBoolean() {
    return bValue(this);
  }

  public int asInt() {
    return iValue(this);
  }

  public float asFloat() {
    return fValue(this);
  }

  public String asString() {
    return sValue(this);
  }

  public Object getValAsObj() {
    return (tok == integer ? Integer.valueOf(intValue) : value);
  }

  // math-related Token static methods

  private final static Point3f pt0 = new Point3f();

  /**
   * 
   * @param x
   * @return   Object-wrapped value
   */
  
  public static Object oValue(ScriptVariable x) {
    switch (x == null ? nada : x.tok) {
    case on:
      return Boolean.TRUE;
    case nada:
    case off:
      return Boolean.FALSE;
    case integer:
      return Integer.valueOf(x.intValue);
    default:
      return x.value;
    }
  }

  /**
   * 
   * @param x
   * @return  numeric value -- integer or decimal
   */
  public static Object nValue(Token x) {
    int iValue;
    switch (x == null ? nada : x.tok) {
    case decimal:
      return x.value;
    case integer:
      iValue = x.intValue;
      break;
    case string:
      if (((String) x.value).indexOf(".") >= 0)
        return new Float(toFloat((String) x.value));
      iValue = (int) toFloat((String) x.value);
      break;
    default:
      iValue = 0;
    }
    return Integer.valueOf(iValue);
  }

  // there are reasons to use Token here rather than ScriptVariable
  // some of these functions, in particular iValue, fValue, and sValue
  
  public static boolean bValue(Token x) {
    switch (x == null ? nada : x.tok) {
    case on:
      return true;
    case off:
      return false;
    case integer:
      return x.intValue != 0;
    case decimal:
    case string:
    case list:
      return fValue(x) != 0;
    case bitset:
      return iValue(x) != 0;
    case point3f:
    case point4f:
    case matrix3f:
    case matrix4f:
      return Math.abs(fValue(x)) > 0.0001f;
    default:
      return false;
    }
  }

  public static int iValue(Token x) {
    switch (x == null ? nada : x.tok) {
    case on:
      return 1;
    case off:
      return 0;
    case integer:
      return x.intValue;
    case decimal:
    case list:
    case string:
    case point3f:
    case point4f:
    case matrix3f:
    case matrix4f:
      return (int) fValue(x);
    case bitset:
      return BitSetUtil.cardinalityOf(bsSelect(x));
    default:
      return 0;
    }
  }

  public static float fValue(Token x) {
    switch (x == null ? nada : x.tok) {
    case on:
      return 1;
    case off:
      return 0;
    case integer:
      return x.intValue;
    case decimal:
      return ((Float) x.value).floatValue();
    case list:
      int i = x.intValue;
      String[] list = (String[]) x.value;
      if (i == Integer.MAX_VALUE)
        return list.length;
    case string:
      return toFloat(sValue(x));
    case bitset:
      return iValue(x);
    case point3f:
      return ((Point3f) x.value).distance(pt0);
    case point4f:
      return Measure.distanceToPlane((Point4f) x.value, pt0);
    case matrix3f:
      Point3f pt = new Point3f();
      ((Matrix3f) x.value).transform(pt);
      return pt.distance(pt0);
    case matrix4f:
      Point3f pt1 = new Point3f();
      ((Matrix4f) x.value).transform(pt1);
      return pt1.distance(pt0);
    default:
      return 0;
    }
  }

  @SuppressWarnings("unchecked")
  public static String sValue(Token x) {
    if (x == null)
      return "";
    int i;
    switch (x.tok) {
    case on:
      return "true";
    case off:
      return "false";
    case integer:
      return "" + x.intValue;
    case point3f:
      return Escape.escape((Point3f) x.value);
    case point4f:
      return Escape.escape((Point4f) x.value);
    case matrix3f:
      return Escape.escape((Matrix3f) x.value);
    case matrix4f:
      return Escape.escape((Matrix4f) x.value);
    case bitset:
      return Escape.escape(bsSelect(x), !(x.value instanceof BondSet));
    case list:
      String[] list = (String[]) x.value;
      i = x.intValue;
      if (i <= 0)
        i = list.length - i;
      if (i != Integer.MAX_VALUE)
        return (i < 1 || i > list.length ? "" : list[i - 1]);
      StringBuffer sb = new StringBuffer();
      for (i = 0; i < list.length; i++)
        sb.append(list[i]).append("\n");
      return sb.toString();
    case hash:
      StringBuffer sbh = new StringBuffer();
      Map<String, ScriptVariable> ht = (Map<String, ScriptVariable>) x.value;
      Object[] keys = ht.keySet().toArray();
      Arrays.sort(keys);
      for (i = 0; i < keys.length; i++) {
        sbh.append(keys[i]).append("\t:");
        String value = ScriptVariable.sValue(ScriptVariable.getVariable(ht.get(keys[i])));
        sbh.append(value.indexOf("\n") >= 0 ? "\n" : "\t");
        sbh.append(value).append("\n");
      }
      return sbh.toString();
    case string:
      String s = (String) x.value;
      i = x.intValue;
      if (i <= 0)
        i = s.length() - i;
      if (i == Integer.MAX_VALUE)
        return s;
      if (i < 1 || i > s.length())
        return "";
      return "" + s.charAt(i - 1);
    case decimal:
    default:
      return "" + x.value;
    }
  }

  private static float toFloat(String s) {
    if (s.equalsIgnoreCase("true"))
      return 1;
    if (s.equalsIgnoreCase("false") || s.length() == 0)
      return 0;
    return Parser.parseFloatStrict(s);
  }

  public static String[] concatList(ScriptVariable x1, ScriptVariable x2) {
    String[] list1 = (x1.tok == list ? (String[]) x1.value : TextFormat.split(
        sValue(x1), "\n"));
    String[] list2 = (x2.tok == list ? (String[]) x2.value : TextFormat.split(
        sValue(x2), "\n"));
    String[] list = new String[list1.length + list2.length];
    int pt = 0;
    for (int i = 0; i < list1.length; i++)
      list[pt++] = list1[i];
    for (int i = 0; i < list2.length; i++)
      list[pt++] = list2[i];
    return list;
  }

  public static BitSet bsSelect(Token token) {
    token = selectItem(token, Integer.MIN_VALUE);
    return (BitSet) token.value;
  }

  public static BitSet bsSelect(ScriptVariable var) {
    if (var.index == Integer.MAX_VALUE)
      var = selectItem(var);
    return (BitSet) var.value;
  }

  public static BitSet bsSelect(Token token, int n) {
    token = selectItem(token);
    token = selectItem(token, 1);
    token = selectItem(token, n);
    return (BitSet) token.value;
  }

  public static ScriptVariable selectItem(ScriptVariable var) {
    // pass bitsets created by the select() or for() commands
    // and all arrays by reference
    if (var.index != Integer.MAX_VALUE || 
        var.tok == list && var.intValue == Integer.MAX_VALUE)
      return var;
    return selectItem(var, Integer.MIN_VALUE);
  }

  public static Token selectItem(Token var) {
    return selectItem(var, Integer.MIN_VALUE);
  }

  public static ScriptVariable selectItem(ScriptVariable var, int i2) {
    return (ScriptVariable) selectItem((Token) var, i2);
  }

  public static Token selectItem(Token tokenIn, int i2) {
    switch (tokenIn.tok) {
    case matrix3f:
    case matrix4f:
    case bitset:
    case list:
    case string:
      break;
    default:
      return tokenIn;
    }

    // negative number is a count from the end

    BitSet bs = null;
    String[] st = null;
    String s = null;

    int i1 = tokenIn.intValue;
    if (i1 == Integer.MAX_VALUE) {
      // no selections have been made yet --
      // we just create a new token with the
      // same bitset and now indicate either
      // the selected value or "ALL" (max_value)
      if (i2 == Integer.MIN_VALUE)
        i2 = i1;
      return new ScriptVariable(tokenIn.tok, i2, tokenIn.value);
    }
    int len = 0;
    boolean isInputSelected = (tokenIn instanceof ScriptVariable && ((ScriptVariable) tokenIn).index != Integer.MAX_VALUE);
    ScriptVariable tokenOut = new ScriptVariable(tokenIn.tok, Integer.MAX_VALUE);

    switch (tokenIn.tok) {
    case bitset:
      if (tokenIn.value instanceof BondSet) {
        tokenOut.value = new BondSet((BitSet) tokenIn.value,
            ((BondSet) tokenIn.value).getAssociatedAtoms());
        bs = (BitSet) tokenOut.value;
        len = BitSetUtil.cardinalityOf(bs);
        break;
      }
      bs = BitSetUtil.copy((BitSet) tokenIn.value);
      len = (isInputSelected ? 1 : BitSetUtil.cardinalityOf(bs));
      tokenOut.value = bs;
      break;
    case list:
      st = (String[]) tokenIn.value;
      len = st.length;
      break;
    case string:
      s = (String) tokenIn.value;
      len = s.length();
      break;
    case matrix3f:
      len = -3;
      break;
    case matrix4f:
      len = -4;
      break;
    }

    if (len < 0) {
      // matrix mode [1][3] or [13]
      len = -len;
      if (i1 > 0 && Math.abs(i1) > len) {
        int col = i1 % 10;
        int row = (i1 - col) / 10;
        if (col > 0 && col <= len && row <= len) {
          if (tokenIn.tok == matrix3f)
            return new ScriptVariable(decimal, new Float(
                ((Matrix3f) tokenIn.value).getElement(row - 1, col - 1)));
          return new ScriptVariable(decimal, new Float(
              ((Matrix4f) tokenIn.value).getElement(row - 1, col - 1)));
        }
        return new ScriptVariable(string, "");
      }
      if (Math.abs(i1) > len)
        return new ScriptVariable(string, "");
      float[] data = new float[len];
      if (len == 3) {
        if (i1 < 0)
          ((Matrix3f) tokenIn.value).getColumn(-1 - i1, data);
        else
          ((Matrix3f) tokenIn.value).getRow(i1 - 1, data);
      } else {
        if (i1 < 0)
          ((Matrix4f) tokenIn.value).getColumn(-1 - i1, data);
        else
          ((Matrix4f) tokenIn.value).getRow(i1 - 1, data);
      }
      if (i2 == Integer.MIN_VALUE)
        return getVariable(data);
      if (i2 < 1 || i2 > len)
        return new ScriptVariable(string, "");
      return getVariable(new Float(data[i2 - 1]));
    }

    // "testing"[0] gives "g"
    // "testing"[-1] gives "n"
    // "testing"[3][0] gives "sting"
    // "testing"[-1][0] gives "ng"
    // "testing"[0][-2] gives just "g" as well
    if (i1 <= 0)
      i1 = len + i1;
    if (i1 < 1)
      i1 = 1;
    if (i2 == 0)
      i2 = len;
    else if (i2 < 0)
      i2 = len + i2;

    if (i2 > len)
      i2 = len;
    else if (i2 < i1)
      i2 = i1;

    switch (tokenIn.tok) {
    case bitset:
      if (isInputSelected) {
        if (i1 > 1)
          bs.clear();
        break;
      }
      int n = 0;
      for (int j = bs.nextSetBit(0); j >= 0; j = bs.nextSetBit(j + 1))
        if (++n < i1 || n > i2)
          bs.clear(j);
      break;
    case string:
      if (i1 < 1 || i1 > len)
        tokenOut.value = "";
      else
        tokenOut.value = s.substring(i1 - 1, i2);
      break;
    case list:
      if (i1 < 1 || i1 > len || i2 > len)
        return new ScriptVariable(string, "");
      if (i2 == i1)
        return fromString(st[i1 - 1]);
      String[] list = new String[i2 - i1 + 1];
      for (int i = 0; i < list.length; i++)
        list[i] = st[i + i1 - 1];
      tokenOut.value = list;
      break;
    }
    return tokenOut;
  }

  /**
   * 
   * @param str
   * @return   ScriptVariable based on string
   */
  public static ScriptVariable fromString(String str) {
    Object v = unescapePointOrBitsetAsVariable(str);
    if (!(v instanceof String))
      return (ScriptVariable) v;
    String s = (String) v;
    if (s.toLowerCase() == "true")
      return getBoolean(true);
    if (s.toLowerCase() == "false")
      return getBoolean(false);
    float f = Parser.parseFloatStrict(s);
    return (Float.isNaN(f) ? new ScriptVariable(string, v) 
        : s.indexOf(".") < 0 ? new ScriptVariable(integer, (int) f)
        : new ScriptVariable(decimal, new Float(f)));
  }

  public boolean setSelectedValue(int selector, ScriptVariable var) {
    if (selector == Integer.MAX_VALUE)
      return false;
    switch (tok) {
    case matrix3f:
    case matrix4f:
      int len = (tok == matrix3f ? 3 : 4);
      if (selector > 10) {
        int col = selector % 10;
        int row = (selector - col) / 10;
        if (col > 0 && col <= len && row <= len) {
          if (tok == matrix3f)
            ((Matrix3f) value).setElement(row - 1, col - 1, fValue(var));
          else
            ((Matrix4f) value).setElement(row - 1, col - 1, fValue(var));
          return true;
        }
      }
      if (selector != 0 && Math.abs(selector) <= len
          && var.value instanceof String[]) {
        String[] s = (String[]) var.value;
        if (s.length == len) {
          float[] data = new float[len];
          for (int i = 0; i < len; i++)
            data[i] = toFloat(s[i]);
          if (selector > 0) {
            if (tok == matrix3f)
              ((Matrix3f) value).setRow(selector - 1, data);
            else
              ((Matrix4f) value).setRow(selector - 1, data);
          } else {
            if (tok == matrix3f)
              ((Matrix3f) value).setColumn(-1 - selector, data);
            else
              ((Matrix4f) value).setColumn(-1 - selector, data);
          }
          return true;
        }
      }
      return false;
    case string:
      String str = (String) value;
      int pt = str.length();
      if (selector <= 0)
        selector = pt + selector;
      if (--selector < 0)
        selector = 0;
      while (selector >= str.length())
        str += " ";
      value = str.substring(0, selector) + sValue(var)
          + str.substring(selector + 1);
      return true;
    case list:
      String[] array = (String[]) value;
      if (selector <= 0)
        selector = array.length + selector;
      if (--selector < 0)
        selector = 0;
      String[] arrayNew = array;
      if (arrayNew.length <= selector) {
        value = arrayNew = ArrayUtil.ensureLength(array, selector + 1);
        for (int i = array.length; i <= selector; i++)
          arrayNew[i] = "";
      }
      arrayNew[selector] = sValue(var);
      return true;
    }
    return false;
  }

  public String escape() {
    switch (tok) {
    case on:
      return "true";
    case off:
      return "false";
    case integer:
      return "" + intValue;
    case bitset:
      return Escape.escape((BitSet)value);
    case list:
      return Escape.escape((String[])value, true);
    case point3f:
      return Escape.escape((Point3f)value);
    case point4f:
      return Escape.escape((Point4f)value);
    case matrix3f:
      return Escape.escape((Matrix3f)value);
    case matrix4f:
      return Escape.escape((Matrix4f)value);
    default:
      return Escape.escape(value);
    }
  }

  public static Object unescapePointOrBitsetAsVariable(String s) {
    if (s == null || s.length() == 0)
      return s;
    Object v = Escape.unescapePointOrBitsetOrMatrixOrArray(s);
    if (v instanceof Point3f)
      return (new ScriptVariable(point3f, v));
    if (v instanceof Point4f)
      return new ScriptVariable(point4f, v);
    if (v instanceof BitSet) {
      if (s.indexOf("[{") == 0)
        v = new BondSet((BitSet) v);
      return new ScriptVariable(bitset, v);
    }
    if (v instanceof Matrix3f)
      return (new ScriptVariable(matrix3f, v));
    if (v instanceof Matrix4f)
      return new ScriptVariable(matrix4f, v);
    return s;
  }

  public static ScriptVariable getBoolean(boolean value) {
    return new ScriptVariable(value ? vT : vF);
  }
  
  public static Object sprintf(String strFormat, ScriptVariable var) {
    if (var == null)
      return strFormat;
    int[] vd = (strFormat.indexOf("d") >= 0 || strFormat.indexOf("i") >= 0 ? new int[1]
        : null);
    float[] vf = (strFormat.indexOf("f") >= 0 ? new float[1] : null);
    double[] ve = (strFormat.indexOf("e") >= 0 ? new double[1] : null);
    boolean getS = (strFormat.indexOf("s") >= 0);
    boolean getP = (strFormat.indexOf("p") >= 0 && var.tok == point3f
        || strFormat.indexOf("q") >= 0 && var.tok == point4f);
    Object[] of = new Object[] { vd, vf, ve, null, null};
    if (var.tok != list)
      return sprintf(strFormat, var, of, vd, vf, ve, getS, getP);
    String[] list = (String[]) var.value;
    String[] list2 = new String[list.length];
    for (int i = 0; i < list.length; i++) {
      String s = strFormat;
      list2[i] = sprintf(s, fromString(list[i]), of, vd, vf, ve, getS, getP);
    }
    return list2;
  }

  private static String sprintf(String strFormat, ScriptVariable var, Object[] of, 
                                int[] vd, float[] vf, double[] ve, boolean getS, boolean getP) {
    if (vd != null)
      vd[0] = iValue(var);
    if (vf != null)
      vf[0] = fValue(var);
    if (ve != null)
      ve[0] = fValue(var);
    if (getS)
      of[3] = sValue(var);
    if (getP)
      of[4]= var.value;
    return TextFormat.sprintf(strFormat, of );
  }

  /**
   * sprintf       accepts arguments from the format() function
   *               First argument is a format string.
   * @param args
   * @return       formatted string
   */
  public static String sprintf(ScriptVariable[] args) {
    switch(args.length){
    case 0:
      return "";
    case 1:
      return sValue(args[0]);
    }
    String[] format = TextFormat.split(TextFormat.simpleReplace(sValue(args[0]), "%%","\1"), '%');
    StringBuffer sb = new StringBuffer();
    sb.append(format[0]);
    for (int i = 1; i < format.length; i++) {
      Object ret = sprintf(TextFormat.formatCheck("%" + format[i]), (i < args.length ? args[i] : null));
      if (ret instanceof String[]) {
        String[] list = (String[]) ret;
        for (int j = 0; j < list.length; j++)
          sb.append(list[j]).append("\n");
        continue;
      }
      sb.append(ret);
    }
    return sb.toString();
  }
  
  @Override
  public String toString() {
    return super.toString() + "[" + name + "] index =" + index + " hashcode=" + hashCode();
  }

  public static BitSet getBitSet(ScriptVariable x, boolean allowNull) {
    switch (x.tok) {
    case Token.bitset:
      return bsSelect(x);
    case Token.list:
      return Escape.unEscapeBitSetArray((String[]) x.value, allowNull);
    }
    return (allowNull ? null : new BitSet());
  }

  public static boolean areEqual(ScriptVariable x1, ScriptVariable x2) {
    if (x1.tok == Token.string && x2.tok == Token.string)
      return ScriptVariable.sValue(x1).equalsIgnoreCase(
          ScriptVariable.sValue(x2));
    if (x1.tok == Token.point3f && x2.tok == Token.point3f)
      return (((Point3f) x1.value).distance((Point3f) x2.value) < 0.000001);
    if (x1.tok == Token.point4f && x2.tok == Token.point4f)
      return (((Point4f) x1.value).distance((Point4f) x2.value) < 0.000001);
    return (Math.abs(ScriptVariable.fValue(x1)
        - ScriptVariable.fValue(x2)) < 0.000001);
  }

}
